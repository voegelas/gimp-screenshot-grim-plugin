#!/usr/bin/python3

# SPDX-License-Identifier: ISC

# GIMP plug-in for taking screenshots of Wayland desktops
#
# Copyright (C) 2025 Andreas Vögele <andreas@andreasvoegele.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

gi.require_version("GimpUi", "3.0")
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

import errno, subprocess, sys, tempfile, time


# Localize the module

import gettext, os

plugindir = os.path.dirname(__file__)
localedir = os.path.join(plugindir, "locale")
if not os.path.isdir(localedir):
    localedir = None

try:
    t = gettext.translation("gimp-screenshot-grim-plugin", localedir)
    _ = t.gettext
except:
    # fmt: off
    def _(message): return message


def slurp():
    args = ["slurp", "-d"]
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise OSError(errno.EINVAL, proc.stderr)
    return proc.stdout.rstrip()


def grim(
    file,
    include_pointer=False,
    level=None,
    output=None,
    quality=None,
    region=None,
    scale_factor=None,
    type=None,
):
    args = ["grim"]
    if include_pointer:
        args.append("-c")
    if level is not None:
        args.append("-l")
        args.append(str(level))
    if output is not None and output != "":
        args.append("-o")
        args.append(output)
    if quality is not None:
        args.append("-q")
        args.append(str(quality))
    if region is not None and region != "":
        args.append("-g")
        args.append(region)
    if scale_factor is not None:
        args.append("-s")
        args.append(str(scale_factor))
    if type is not None:
        args.append("-t")
        args.append(type)
    args.append("-")
    proc = subprocess.Popen(args, stdout=file, stderr=subprocess.PIPE)
    try:
        _, errs = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, errs = proc.communicate()
    if proc.returncode != 0:
        raise OSError(errno.EINVAL, str(errs, errors="ignore"))


def shoot_dialog(procedure, config):
    names = [_.name for _ in procedure.get_arguments() if _.name != "run-mode"]
    dialog = GimpUi.ProcedureDialog(
        procedure=procedure, config=config, title=_("Screenshot")
    )
    dialog.set_ok_label(_("S_nap"))
    dialog.fill(names)
    ok = dialog.run()
    dialog.destroy()
    return ok


def screenshot_run(procedure, config, data):
    run_mode = config.get_property("run-mode")

    output = ""
    region = ""

    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init("plug-in-screenshot-grim")
        if not shoot_dialog(procedure, config):
            return procedure.new_return_values(
                Gimp.PDBStatusType.CANCEL,
                GLib.Error(),
            )

    shoot_type = config.get_property("shoot-type")
    include_pointer = config.get_property("include-pointer")
    screenshot_delay = config.get_property("screenshot-delay")

    if screenshot_delay > 0:
        time.sleep(screenshot_delay)

    if shoot_type == "region":
        try:
            region = slurp()
            if region == "":
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CANCEL,
                    GLib.Error(),
                )
        except Exception as e:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(str(e)),
            )
    elif shoot_type == "output":
        output = config.get_property("output")
        if output == "":
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error(_("Missing Wayland output name")),
            )
    elif shoot_type == "rectangle":
        x1 = config.get_property("x1")
        y1 = config.get_property("y1")
        x2 = config.get_property("x2")
        y2 = config.get_property("y2")
        if x2 < x1 or y2 < y1:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error(_("Invalid rectangle coordinates")),
            )
        region = f"{x1},{y1} {x2 - x1 + 1}x{y2 - y1 + 1}"
    else:
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error(_("Unknown shoot type") + ": " + shoot_type),
        )

    with tempfile.NamedTemporaryFile(
        mode="wb", delete_on_close=False, suffix=".ppm"
    ) as fp:
        try:
            grim(
                fp,
                include_pointer=include_pointer,
                output=output,
                region=region,
                type="ppm",
            )
        except Exception as e:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(str(e)),
            )
        finally:
            fp.close()
        image = Gimp.file_load(
            Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(fp.name)
        )
        if image is None:
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR,
                GLib.Error(_("Cannot load screenshot")),
            )
        Gimp.Display.new(image)
        return Gimp.ValueArray.new_from_values(
            [
                GObject.Value(Gimp.PDBStatusType, Gimp.PDBStatusType.SUCCESS),
                GObject.Value(Gimp.Image, image),
            ]
        )


class ScreenshotGrim(Gimp.PlugIn):
    _attribution = (
        "Andreas Vögele",  # Authors
        "Andreas Vögele",  # Copyright holders
        "2025",
    )

    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        return ["plug-in-screenshot-grim"]

    def do_create_procedure(self, name):
        if name == "plug-in-screenshot-grim":
            return self._create_procedure_screenshot_grim(name)
        return None

    def _create_procedure_screenshot_grim(self, name):
        procedure = Gimp.Procedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            screenshot_run,
            None,
        )
        procedure.set_menu_label(_("Screenshot with grim..."))
        procedure.set_documentation(
            _("Create an image from a region of a Wayland desktop"),
            _(
                "This plug-in takes a screenshot of a desktop region. "
                "The utilities grim and slurp are required."
            ),
            name,
        )
        procedure.set_attribution(*self._attribution)
        procedure.add_menu_path("<Image>/File/Create")
        procedure.add_enum_argument(
            "run-mode",
            _("Run mode"),
            _("The run mode"),
            Gimp.RunMode,
            Gimp.RunMode.NONINTERACTIVE,
            GObject.ParamFlags.READWRITE,
        )
        shoot_type_choice = Gimp.Choice.new()
        shoot_type_choice.add(
            "region",
            0,
            _("Select a region to capture"),
            _("Move the selection with space bar held or cancel with Esc"),
        )
        shoot_type_choice.add(
            "output",
            1,
            _("Capture an entire Wayland output"),
            _('Pass the output name in "output"'),
        )
        shoot_type_choice.add(
            "rectangle",
            2,
            _("Capture a region by coordinates"),
            _('Pass the coordinates in "x1", "y1", "x2" and "y2"'),
        )
        procedure.add_choice_argument(
            "shoot-type",
            _("Shoot _area"),
            _("The shoot type"),
            shoot_type_choice,
            "region",
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_string_argument(
            "output",
            _("_Wayland output"),
            _("The name of the Wayland output to capture"),
            "",
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_int_argument(
            "x1",
            _("Le_ft coordinate x1"),
            _("Left x-coordinate"),
            GLib.MININT,
            GLib.MAXINT,
            0,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_int_argument(
            "y1",
            _("_Top coordinate y1"),
            _("Top y-coordinate"),
            GLib.MININT,
            GLib.MAXINT,
            0,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_int_argument(
            "x2",
            _("R_ight coordinate x2"),
            _("Right x-coordinate"),
            GLib.MININT,
            GLib.MAXINT,
            0,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_int_argument(
            "y2",
            _("_Bottom coordinate y2"),
            _("Bottom y-coordinate"),
            GLib.MININT,
            GLib.MAXINT,
            0,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_boolean_argument(
            "include-pointer",
            _("Include _mouse pointer"),
            _("Your pointing device's cursor will be part of the image"),
            False,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_int_argument(
            "screenshot-delay",
            _("Screenshot dela_y"),
            _("Delay before taking the screenshot"),
            0,
            20,
            0,
            GObject.ParamFlags.READWRITE,
        )
        procedure.add_image_return_value(
            "image",
            _("Image"),
            _("Screenshot"),
            False,
            GObject.ParamFlags.READWRITE,
        )
        return procedure


Gimp.main(ScreenshotGrim.__gtype__, sys.argv)

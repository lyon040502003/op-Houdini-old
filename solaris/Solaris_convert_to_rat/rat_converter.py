import hou
from pxr import Usd
import os

# getting the stage and then right nodes
node = hou.pwd()
ls = hou.LopSelectionRule()
ls.setPathPattern("%type:Shader")
paths = ls.expandedPaths(node.inputs()[0])
stage = node.editableStage()

# infos about the inner nodes of the subnet and where tey are
paren_subnet = hou.node(".").parent()
py_script = hou.node(".")
inline_usd = hou.node(paren_subnet.path() + "/inlineusd1")
info_store = hou.node(paren_subnet.path() + "/info_store")
print_on = info_store.parm("print_out").eval()


texture_file_types = (
    "pic",
    "picgz",
    "picZ",
    "rat",
    "picnc",
    "ratnc",
    "png",
    "psd",
    "psb",
    "cin",
    "kdk",
    "hdr",
    "fit",
    "gif",
    "gif89",
    "ies",
    "jpg",
    "jpeg",
    "qtl",
    "rla",
    "rlb",
    "rla16",
    "r16",
    "r32",
    "pix",
    "sgi",
    "rgb",
    "rgba",
    "si",
    "pic",
    "tif",
    "tiff",
    "tif3",
    "tif16",
    "tx",
    "tga",
    "vst",
    "vtg",
    "yuv",
    "exr",
)


def get_objects_and_files(expandedPaths):
    found = []

    for path in expandedPaths:
        object = stage.GetPrimAtPath(path)
        for atts in object.GetAttributes():
            info = str(
                object.GetAttribute(str(atts).split(".")[-1].split("'")[-2]).Get()
            )
            if "@" in info:
                if (
                    info.split("@")[-2]
                    .split(".")[-1]
                    .lower()
                    .endswith(texture_file_types)
                ):
                    paren_usd_file = (
                        str(object.GetPrimStack()[-1]).split(",")[-2].split("'")[-2]
                    )
                    add = [str(object.GetPath()), info.split("@")[-2]]
                    if print_on:
                        print("object", path)
                        print("attribute", atts)
                        print("file", info)
                        print("-" * 80)
                        print()

                    if os.path.exists(paren_usd_file):
                        add.append(paren_usd_file)
                    else:
                        add.append(hou.hipFile.path())

                    found.append(add)

    return found


def resolve_relative_paths(dict):
    for pos, i in enumerate(dict):
        if not os.path.exists(i[1]):
            os.chdir(os.path.dirname(i[2]))
            found[pos] = [i[0], os.path.abspath(i[1]), i[2]]


found = get_objects_and_files(paths)
resolve_relative_paths(found)


def overwrite_and_convert_to_rat(file_to_convert, overwrite_stage, info_store_node):
    all_generated_files = []
    file_to_convert_without_duplication = dict()

    # recompose to dict to make shure every file only exists once // this is an error from a poor choise off storage system
    for i in file_to_convert:
        file = i[1]
        node_and_paren_file = [i[0], i[2]]
        try:
            file_to_convert_without_duplication[i[1]].append(node_and_paren_file)
        except:
            file_to_convert_without_duplication[i[1]] = [node_and_paren_file]

    for i in file_to_convert_without_duplication:
        Hou_dir = os.path.abspath(hou.houdiniPath()[-1])
        iconver_exe = "\iconvert.exe"
        in_file = i
        file_out = "auto_convert_temp_" + in_file.split("/")[-1].split(".")[0] + ".rat"

        if os.path.exists(file_out):
            os.remove(file_out)

        cmd_iconvert_command = (
            "-g auto  -d float  "
            + in_file
            + "  "
            + os.path.dirname(in_file)
            + "/"
            + file_out
        )
        cmd_command = '"' + Hou_dir + iconver_exe + '" ' + cmd_iconvert_command
        os.system(cmd_command)

        for node in file_to_convert_without_duplication[i]:
            object = overwrite_stage.GetPrimAtPath(node[0])
            object.GetAttribute("inputs:file").Set(
                os.path.dirname(in_file) + "/" + file_out
            )

        all_generated_files.append(os.path.dirname(in_file) + "/" + file_out)

    info_store_node.parm("rat_conv_info_store").set(str(all_generated_files))


def conv():
    # Find all the sublayers in the main stage
    sublayers = []
    sublayers.append(stage.GetRootLayer().identifier)
    for i in stage.GetRootLayer().subLayerPaths:
        sublayers.append(i)

    # Create empty stage that only exists in memory
    Over_write_stage = Usd.Stage.CreateInMemory()
    # add sublayers to the empty overwrite stage
    Over_write_stage.GetRootLayer().subLayerPaths = sublayers

    # --- This is the portion off the script where the changes to inline usd need to be made ---

    # Reloading all the texture chaches becuase houdini somtimes hase problems applying the change
    # The relode is curently deactivated because it works offten enought and the reloade for bigger sceeses is to slow
    # hou.hscript("texcache -c")
    # hou.hscript("glcache -c")

    overwrite_and_convert_to_rat(found, Over_write_stage, info_store)

    # delet all the sublayers off the overwrite stage and keep all the changes that where made.
    Over_write_stage.GetRootLayer().subLayerPaths = []
    # convert the stage that only stores the changes to usda and then save as string for export.
    usd_overwrite = Over_write_stage.ExportToString()

    # set the overwirte in to the inline usd node present in the hda

    inline_usd.parm("usdsource").set(usd_overwrite)


# ---- toodos -----

# TODO The script updates on all changes and not only texture changes. needs a way to to do "nothing" when the cahge was no texture change.

import hou
import os


def clean():
    paren_subnet = hou.node(".").parent()
    py_script = hou.node(".")
    inline_usd = hou.node(paren_subnet.path() + "/inlineusd1")
    info_store = hou.node(paren_subnet.path() + "/info_store")

    converted_files = (
        info_store.parm("rat_conv_info_store")
        .eval()
        .strip("[]")
        .replace("'", "")
        .replace(" ", "")
        .split(",")
    )
    print_on = info_store.parm("print_out").eval()

    hou.hscript("texcache -c")
    hou.hscript("glcache -c")
    for file in converted_files:
        if os.path.exists(file):
            os.remove(file)
            if print_on:
                print("deleted:", file)
        else:
            if print_on:
                print("no_file_with_this_path:", file)

    paren_subnet.parm("Suspend").set(1)
    paren_subnet.parm("Auto_update").set(0)
    print("par", paren_subnet)

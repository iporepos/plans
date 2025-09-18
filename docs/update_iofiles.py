import pandas as pd


def dataframe_to_rst(df):
    header = df.columns.tolist()
    max_widths = [max(df[col].astype(str).apply(len).max(), len(col)) for col in header]

    def format_row(row):
        return (
            "| " + " | ".join(f"{x:<{max_widths[i]}}" for i, x in enumerate(row)) + " |"
        )

    rst_table = "+" + "+".join(["-" * (w + 2) for w in max_widths]) + "+\n"
    rst_table += format_row(header) + "\n"
    rst_table += "+" + "+".join(["=" * (w + 2) for w in max_widths]) + "+\n"

    for _, row in df.iterrows():
        rst_table += format_row(row) + "\n"
        rst_table += "+" + "+".join(["-" * (w + 2) for w in max_widths]) + "+\n"

    return rst_table


def get_admoenition(msg, kind="note"):
    lst_adm = []
    lst_adm.append("")
    lst_adm.append(".. {}::".format(kind))
    lst_adm.append("")
    lst_adm.append("\t{}".format(msg))
    lst_adm.append("")
    lst_adm.append("")
    return lst_adm


def get_fields(fields_string):
    lst_fields_out = []
    lst_fields = fields_string.split("&")
    for field in lst_fields:
        s_name = field.split(":")[0].strip()
        s_desc = field.split(":")[1].strip()
        lst_fields_out.append("\t - ``{}``: {}".format(s_name, s_desc))
    return lst_fields_out


df = pd.read_csv("../plans/iofiles.csv", sep=";")

# INPUT CATALOG

df_input = df.query("io == 'inputs'")

df_input_rst = df_input.drop_duplicates(subset="File")
print(dataframe_to_rst(df_input_rst[["File", "Structure", "Description"]]))


# inputs lines
lst_input = []

# RASTER files
dict_refs = {"raster": "[`io-raster`_]", "qraster": "[`io-qualiraster`_]"}
df_files = df_input.query("Format == 'raster' or Format == 'qraster'")
df_files = df_files.drop_duplicates(subset="File")
df_files = df_files.sort_values(by="File", ascending=True)
for i in range(len(df_files)):
    lst_input.append("``{}``".format(df_files["File"].values[i]))
    lst_input.append("-" * 60)
    str_ref = dict_refs[df_files["Format"].values[i]]
    lst_input.append("{} {}".format(str_ref, df_files["Description"].values[i]))
    lst_input.append("")
    lst_input.append(" - Map Units: {}".format(df_files["Map Units"].values[i]))
    # handle suffix:
    lcl_suff = df_files["Suffix"].values[i]
    if lcl_suff == "-":
        pass
    else:
        lst_input.append(" - Suffix: {}".format(lcl_suff))
    # handle folders
    df_folders = df_input.query("File == '{}'".format(df_files["File"].values[i]))
    lst_folders = df_folders["Folder"].values
    if len(lst_folders) == 0:
        str_folder = "``" + lst_folders[0] + "``"
    else:
        lst_folders = ["``{}``".format(f) for f in lst_folders]
        str_folder = "; ".join(lst_folders)
    lst_input.append(" - Expected in folder(s): {}".format(str_folder + "."))
    lst_input.append("")

    # handle admoenitions
    # note
    lcl_admoe = df_files["Note"].values[i]
    if lcl_admoe == "-":
        pass
    else:
        lst_admoe = get_admoenition(msg=lcl_admoe, kind="note")
        for l in lst_admoe:
            lst_input.append(l)
    # warning
    lcl_admoe = df_files["Warning"].values[i]
    if lcl_admoe == "-":
        pass
    else:
        lst_admoe = get_admoenition(msg=lcl_admoe, kind="warning")
        for l in lst_admoe:
            lst_input.append(l)
    lst_input.append("")

# Table files
dict_refs = {
    "Time series": "[`io-timeseries`_]",
    "Attribute table": "[`io-attribute`_]",
}
dict_fields = {
    "Time series": "Datetime: Timestamp in the format YYYY-MM-DD HH:mm:ss",
    "Attribute table": "Id: Unique Id number (integer) & Name: Unique name & Alias: Unique short name & Color: Unique color code",
}
df_files = df_input.query(
    "Structure == 'Time series' or Structure == 'Attribute table'"
)
df_files = df_files.drop_duplicates(subset="File")
df_files = df_files.sort_values(by="File", ascending=True)
for i in range(len(df_files)):
    lst_input.append("``{}``".format(df_files["File"].values[i]))
    lst_input.append("-" * 60)
    str_ref = dict_refs[df_files["Structure"].values[i]]
    lst_input.append("{} {}".format(str_ref, df_files["Description"].values[i]))
    lst_input.append("")

    # Fields
    lst_input.append(" - Basic Fields:")
    lst_basic_fields = get_fields(
        fields_string=dict_fields[df_files["Structure"].values[i]]
    )
    for l in lst_basic_fields:
        lst_input.append(l)
    lst_input.append("")
    lst_input.append(" - Extra Fields:")
    lst_extra_fields = get_fields(fields_string=df_files["Fields"].values[i])
    for l in lst_extra_fields:
        lst_input.append(l)
    lst_input.append("")
    # handle suffix:
    lcl_suff = df_files["Suffix"].values[i]
    if lcl_suff == "-":
        pass
    else:
        lst_input.append(" - Suffix: {}".format(lcl_suff))

    # handle folders
    df_folders = df_input.query("File == '{}'".format(df_files["File"].values[i]))
    lst_folders = df_folders["Folder"].values
    if len(lst_folders) == 0:
        str_folder = "``" + lst_folders[0] + "``"
    else:
        lst_folders = ["``{}``".format(f) for f in lst_folders]
        str_folder = "; ".join(lst_folders)
    lst_input.append(" - Expected in folder(s): {}".format(str_folder + "."))
    lst_input.append("")

    # handle admoenitions
    # note
    lcl_admoe = df_files["Note"].values[i]
    if lcl_admoe == "-":
        pass
    else:
        lst_admoe = get_admoenition(msg=lcl_admoe, kind="note")
        for l in lst_admoe:
            lst_input.append(l)
    # warning
    lcl_admoe = df_files["Warning"].values[i]
    if lcl_admoe == "-":
        pass
    else:
        lst_admoe = get_admoenition(msg=lcl_admoe, kind="warning")
        for l in lst_admoe:
            lst_input.append(l)
    lst_input.append("")


for l in lst_input:
    print(l)

lst_input = ["{}\n".format(line) for line in lst_input]

f = open("./input_catalog.rst", "w")
f.writelines(lst_input)
f.close()

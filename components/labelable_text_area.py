# https://www.tutorialspoint.com/python/tk_text.htm
from tkinter import Frame, Text, LabelFrame, Menu, Button
from tkinter.constants import *

from moustovtkwidgets_lib.mtk_edit_table import mtkEditTable

from components.color_utility import random_color
from components.labelable_text_area_listener import LabelableTextAreaListener
from components.labels_treeview import LabelTreeview


class LabelableTextArea(LabelableTextAreaListener):
    def __init__(self, frame: Frame, listener: LabelableTextAreaListener):
        self.labels_treeview = None
        self.labels_content_widget = None
        self.validate_text_button = None
        self.frame = frame
        self.listener = listener
        self.area_text = None
        self.local_frame = None
        self.local_content_labelframe = LabelFrame(self.frame, text='Text detail')
        self.local_frame = None
        self.menu = None
        self.tags_in_text = {}
        self.tags = {}
        # {"here":
        #     {
        #         "color": "#ABCDAB",
        #         "description": "a description for the label 'here'"
        #     }
        # }

    def assign_label_in_text(self):
        selected_text = self.area_text.selection_get()
        print("selected_text", selected_text)
        text = self.area_text.get(1.0, "end-1c")
        lines = text.split("\n")
        line_id = 1
        beg_pos = -1
        found = False
        # todo select all occurrencies of a selected text
        for line in lines:
            beg_pos = line.find(selected_text)
            if beg_pos >= 0:
                found = True
                break
            line_id += 1
        if found:
            end_pos = beg_pos + len(selected_text)
            # TODO select the right label
            print("here --", beg_pos, text.find(selected_text), line_id, selected_text, f"{line_id}.{beg_pos}",
                  f"{line_id}.{end_pos}")
            self.area_text.tag_add(self.get_current_tag(), f"{line_id}.{beg_pos}", f"{line_id}.{end_pos}")
            self.tags_in_text[f"{line_id}.{beg_pos}"] = {"label": "here", "end": f"{line_id}.{end_pos}",
                                                         "text": selected_text}
            print(f"tags_in_text[{line_id}.{beg_pos}]", self.tags_in_text[f"{line_id}.{beg_pos}"])
        else:
            raise ValueError(f"'{selected_text}' not in '{text}'")

    def _do_update_text_in_treeview(self):
        """
        updates the listener with the Text content, transcription labels & labels
        """
        text = self.area_text.get(1.0, "end-1c")
        print("_do_validate_text", text)
        self.listener.set_new_text(text)
        self.listener.set_transcription_labels(self.tags_in_text)
        # updating self.tags from self.labels_treeview
        self.tags = {}
        json = self.labels_treeview.get_data()
        for rowiid in json.keys():
            label_name = json[rowiid][0]
            description = json[rowiid][1]
            color = json[rowiid][2]
            self.tags[label_name] = {'color': color, 'description': description}
        print("$$$$ _do_update_text_in_treeview", json, self.tags)
        # {'0': ['here', "a description for the label 'here'", '#ABCDAB'],
        #  'I001': ['#BDCDCC', "a description for the label '#BDCDCC'", '#BDCDCC']}
        # {'#BDCDCC': {'color': '#BDCDCC', 'description': "a description for the label '#BDCDCC'"}}
        self.listener.set_labels(self.tags)

    def get_ui_content(self, frame: Frame) -> LabelFrame:
        self.local_frame = LabelFrame(frame)
        #
        self.area_text = Text(self.local_frame, height=5)
        self.area_text.grid(row=0, column=0, sticky="ns")
        #
        self.validate_text_button = Button(self.local_frame, text='Update', command=self._do_update_text_in_treeview)
        self.validate_text_button.grid(row=0, column=1, padx=5, pady=5)
        #
        col_ids = ('label', 'description', 'color')
        col_titles = ('label', 'description', 'color')
        self.labels_content_widget = LabelTreeview(self.local_frame)
        self.local_content_labelframe = self.labels_content_widget.get_ui_content(self.local_frame)
        self.labels_treeview = self.labels_content_widget.label_treeview
        self.local_content_labelframe.grid(row=0, column=2, padx=5, pady=5)
        # right click menu - https://tkdocs.com/tutorial/menus.html
        self.menu = Menu(self.local_frame, tearoff=0)
        self.menu.add_command(label="Assign tag", command=self.assign_label_in_text)
        self.menu.add_command(label="Assign new tag", command=self.add_new_label)
        self.menu.add_separator()
        self.menu.add_command(label="Delete tag", command=self.noop)
        self.area_text.bind("<Button-3>", self._on_right_click)
        return self.local_frame

    def noop(self):
        print("<< did nothing >>")

    def add_new_label(self):
        label_color = new_label_name = random_color()  # the new name is the color
        self.tags[new_label_name] = {}
        self.tags[new_label_name]["color"] = new_label_name
        self.tags[new_label_name]["description"] = f"a description for the label '{new_label_name}'"
        print("### self.tags[new_label_name]", self.tags[new_label_name])
        # add new tag in list
        new_label_values = [new_label_name, self.tags[new_label_name]["description"],
                            self.tags[new_label_name]["color"]]
        self.area_text.tag_configure(new_label_name, background=label_color)
        # assign tag to row
        new_iid = self.labels_treeview.insert(parent="", index='end', text="", tags=new_label_name,
                                              values=tuple(new_label_values))
        self.labels_treeview.tag_configure(new_label_name, background=label_color)
        self.assign_label_in_text()

    def set_text(self, text: str, row_transcription_labels_json: dict, labels_json: dict):
        """
        labeled_text: see (components/transcription_format.json)[components/transcription_format.json]["transcription_labels"]
        :row_transcription_labels_json: the transcription_labels_json of the selected row
                eg. {"1.109": {
                        "label": "here",
                        "end": "1.119",
                        "text": "associatif"
                        }
                    }
        """
        print("lta set_text", text, row_transcription_labels_json, labels_json)
        # remove all previous tags in Text content
        for tag in self.area_text.tag_names():
            self.area_text.tag_remove(tag, "1.0", "end")
        # remove text content
        self.area_text.delete('1.0', END)
        # set to new text
        self.area_text.insert(END, text)
        # set tags in text
        if text:
            print("=== set_text", row_transcription_labels_json)
            for beg_key in row_transcription_labels_json.keys():
                print("row_transcription_labels_json", row_transcription_labels_json)
                print("beg_key", beg_key)
                label = row_transcription_labels_json[str(beg_key)]["label"]
                print("label", label)
                print(f"row_transcription_labels_json[{str(beg_key)}]['label']",
                      row_transcription_labels_json[str(beg_key)]["label"])
                end_key = row_transcription_labels_json[str(beg_key)]["end"]
                print("end_key", end_key)
                selected_text = row_transcription_labels_json[str(beg_key)]["text"]
                print("selected_text", selected_text)
                self.area_text.tag_add(label, beg_key, end_key)
                self.tags_in_text[beg_key] = {"label": label,
                                              "end": end_key,
                                              "text": selected_text}

    def set_label_list_in_labels_treeview(self, labels_json: dict):
        """
        labeled_text: see (components/transcription_format.json)[components/transcription_format.json]["transcription_labels"]
        labels: see (components/transcription_format.json)[components/transcription_format.json]["labels"]
        """
        res_labels = {}
        index = 0
        # add labels into treeview
        print("set_label_list", labels_json)
        for label_name in labels_json.keys():
            print("set_label_list label_name", label_name)
            res_labels[str(index)] = [label_name, labels_json[label_name]["description"],
                                      labels_json[label_name]["color"]]
            index += 1
        print("set_label_list res_labels", res_labels)
        self.labels_treeview.set_data(res_labels)
        # add labels styles and assign to rows
        index = 0
        for label_name in labels_json.keys():
            # define tag in treeview
            print("tag_configure", label_name, labels_json[label_name]["color"])
            self.labels_treeview.tag_configure(label_name, background=labels_json[label_name]["color"])
            # assign tag to row
            self.labels_treeview.item(str(index), tags=label_name)
            # assign tag to self.area_text
            self.area_text.tag_configure(label_name, background=labels_json[label_name]["color"])
            index += 1

    def _on_right_click(self, event):
        print(event)
        self.menu.post(event.x_root, event.y_root)

    def get_tag_color(self, tag: str):
        print("**** get_tag_color", tag, self.tags)
        if self.tags and tag in self.tags.keys():
            return self.tags[tag]["color"]
        raise ValueError(f"the tag {tag} does not exist")

    def get_current_tag(self) -> str:
        print("get_current_tag selected", self.labels_treeview.rowID)
        print("get_current_tag data", self.labels_treeview.get_data())
        row = self.labels_treeview.item(str(self.labels_treeview.rowID))
        print("get_current_tag row", row)
        if row["values"]:
            return row["values"][0]
        else:
            raise ValueError("No tag currently selected")


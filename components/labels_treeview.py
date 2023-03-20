import json
import os
from tkinter import LabelFrame, Scrollbar, Frame
from tkinter.constants import *
from moustovtkwidgets_lib.mtk_edit_table import mtkEditTable, mtkEditTableListener

from components.color_utility import random_color


class LabelTreeview(mtkEditTableListener):
    def __init__(self, frame: LabelFrame):
        self.part_number = 0
        self.frame = frame
        self.horscrlbar = None
        self.verscrlbar = None
        self.label_treeview = None
        self.label_content_labelframe = LabelFrame(self.frame, text='label')
        self.local_frame = None
        self.previous_part = None

    def right_click_fired(self, event):
        """
        event triggered by self.label_tree when a right_click is done and the menu is not yet displayed
        to update the menu
        """
        # adapt menu text to previous existing part
        self.previous_part = ""
        for i in self.label_treeview.get_children():
            print("i == self.label_tree.rowID", i, self.label_treeview.rowID)
            data = self.label_treeview.item(i)['text']
            if data:
                self.previous_part = data
            if i == self.label_treeview.rowID:
                break
        self.label_treeview.menu.entryconfig(6, label=f"Assign rows to part '{self.previous_part}'")
        #
        # disable "Assign rows to previous part" if not existing part
        if self.previous_part:
            self.label_treeview.menu.entryconfig(6, state="normal")
        else:
            self.label_treeview.menu.entryconfig(6, state="disabled")

    def get_ui_content(self, frame: Frame) -> Frame:
        self.local_frame = Frame(frame)
        col_ids = ('label', 'description', 'color')
        col_titles = ('label', 'description', 'color')
        self.label_treeview = mtkEditTable(self.local_frame, columns=col_ids, column_titles=col_titles)
        self.label_treeview.add_listener(self)
        self.label_treeview.debug = True
        self.label_treeview.column('label', anchor=CENTER, width=60, stretch=NO)
        self.label_treeview.column('description', anchor=W, width=200, minwidth=100)
        self.label_treeview.column('color', anchor=CENTER, width=0, stretch=YES)
        self.label_treeview.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.label_treeview.column("#0", width=70, stretch=NO)
        #
        self.verscrlbar = Scrollbar(self.label_content_labelframe,
                                    orient="vertical",
                                    command=self.label_treeview.yview)
        self.verscrlbar.grid(row=0, column=2, sticky="ns")
        self.horscrlbar = Scrollbar(self.label_content_labelframe,
                                    orient="horizontal", width=20,
                                    command=self.label_treeview.xview)
        self.horscrlbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.label_treeview.configure(xscrollcommand=self.horscrlbar.set, yscrollcommand=self.verscrlbar.set)

        self.label_treeview.menu.add_separator()
        self.label_treeview.menu.add_command(label="Move upward", command=self.move_label_upward)
        self.label_treeview.menu.add_command(label="Move downward", command=self.move_label_downward)
        return self.local_frame

    def move_label_downward(self):
        """
        move all row into the previous part
        """
        # selected_row = self.label_tree.item(self.label_tree.rowID)
        print("move_label_downward", self.label_treeview.rowID, self.previous_part)
        # is_inside = False
        # previous_part_id = None
        # pos_in_part = 0
        # for i in self.label_tree.get_children():
        #     data = self.label_tree.item(i)['text']
        #     if data and self.previous_part == data:
        #         is_inside = True
        #         previous_part_id = i
        #     if is_inside and i != previous_part_id:
        #         self.label_tree.move(i, previous_part_id, pos_in_part)
        #         self.label_tree.item(i, tags=self.previous_part)
        #         pos_in_part += 1
        #     if i == self.label_tree.rowID:
        #         break

    def move_label_upward(self):
        print("move_label_upward")
        # selected_values = self.label_tree.item(self.label_tree.rowID)
        # self.previous_part = self.label_tree.rowID
        # values = selected_values.get("values")
        # self.part_number += 1
        # part_name = f"Part#{self.part_number}".replace(" ", "")
        # color = random_color()
        # print(part_name, color)
        # self.label_tree.tag_configure(part_name, background=color)
        # self.label_tree.item(self.label_tree.rowID, text=part_name, values=values, tags=part_name)

    def get_data(self) -> dict:
        return self.label_treeview.get_data()

    def set_data(self, label: dict):
        """
        loads a json label into self.label_tree with colored parts
        json =     "labels": {
                        "here": {
                            "color": "#ABCDAB",
                            "description": "a description for the label 'here'"
                        }
                    }
        """
        print(">> ltv set_data", label)
        self.label_treeview.set_data(label)
        # self.label_treeview.set_data(label["label"])
        # for i in self.label_treeview.get_children():
        #     print("===", i)
        #     text = self.label_treeview.item(i)['text'].replace(" ", "")
        #     if text:
        #         color = random_color()
        #         print(text, color)
        #         self.label_treeview.tag_configure(text, background=color)
        #         self.label_treeview.item(i, tags=text)
        #         for j in self.label_treeview.get_children(i):
        #             self.label_treeview.item(j, tags=text)

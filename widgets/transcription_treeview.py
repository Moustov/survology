from tkinter import LabelFrame, Scrollbar, Frame
from tkinter.constants import *
from moustovtkwidgets_lib.mtk_edit_table import mtkEditTable


class TranscriptionTreeview:
    def __init__(self, frame: Frame):
        self.frame = frame
        self.horscrlbar = None
        self.verscrlbar = None
        self.transcription_tree = None
        self.transcription_content_labelframe = None
        self.local_frame = None

    def get_transcription_frame_pack(self, fill=BOTH, expand=1) -> LabelFrame:
        """
        adds a transcription LabelFrame in a pack-like layout
        """
        self.transcription_content_labelframe = LabelFrame(self.frame, text='Transcription')
        self.transcription_content_labelframe.pack(fill=fill, expand=expand)
        self._add_content()
        return self.transcription_content_labelframe

    def get_transcription_frame_grid(self, row_pos: int, col_pos:int) -> LabelFrame:
        """
        adds a transcription LabelFrame in a pack-like layout
        """
        self.transcription_content_labelframe = LabelFrame(self.frame, text='Transcription')
        self.transcription_content_labelframe.grid(row=row_pos, column=col_pos)
        self._add_content()
        return self.transcription_content_labelframe

    def _add_content(self):
        col_ids = ('chrono', 'Text', 'tags')
        col_titles = ('chrono', 'Text', 'tags')
        self.local_frame = Frame(self.transcription_content_labelframe)
        self.local_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew", ipadx=250, ipady=80)
        self.transcription_tree = mtkEditTable(self.local_frame, columns=col_ids, column_titles=col_titles)
        self.transcription_tree.debug = True
        self.transcription_tree.column('chrono', anchor=CENTER, width=30)
        self.transcription_tree.column('Text', anchor=W, width=120)
        self.transcription_tree.column('tags', anchor=CENTER, width=0, stretch=NO)
        self.transcription_tree.pack(fill=BOTH, expand=True)
        #
        self.verscrlbar = Scrollbar(self.transcription_content_labelframe,
                                    orient="vertical",
                                    command=self.transcription_tree.yview)
        self.verscrlbar.grid(row=0, column=2, sticky="ns")
        self.horscrlbar = Scrollbar(self.transcription_content_labelframe,
                                    orient="horizontal", width=20,
                                    command=self.transcription_tree.xview)
        self.horscrlbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.transcription_tree.configure(xscrollcommand=self.horscrlbar.set, yscrollcommand=self.verscrlbar.set)

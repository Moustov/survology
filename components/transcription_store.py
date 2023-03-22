import json
import os
from copy import deepcopy
from json import JSONDecodeError


class TranscriptionStoreException(Exception):
    def __init__(self, msg: str, **kwargs):
        super().__init__(msg, kwargs)


class TranscriptionStore:
    FILE_FORMAT = "1.0"

    def __init__(self, transcription_name: str):
        self.transcriptions_path = "audio samples"
        # todo replace all forbidden chars https://www.mtu.edu/umc/services/websites/writing/characters-avoid/
        self.transcription_name = transcription_name.replace(':', "_")
        self.file_format = ""
        self.json_parts_colors = {}
        self.json_transcription = {}
        self.json_labels = {}
        self.json_transcription_labels = {}

    def get_audio_file_name(self) -> str:
        res = f"{self.transcriptions_path}/{self.transcription_name}.mp3"
        print("get_audio_file_name", res)
        return res

    def get_json_file_name(self) -> str:
        # todo replace all forbidden chars https://www.mtu.edu/umc/services/websites/writing/characters-avoid/
        res = f"{self.transcriptions_path}/{self.transcription_name}.json"
        print("get_json_file_name", res)
        return res

    def load(self, file_name: str = None, with_audio_file: bool = True):
        """
        loads a json file and feeds the transcription data enclosed
        todo: handle backward compatibility
        """
        if file_name is None:
            file_name = self.get_json_file_name()
        else:
            file_path, file_extension = os.path.splitext(file_name)
            if file_extension.lower() != ".mp3" and with_audio_file:
                raise TranscriptionStoreException("Only MP3 files are taken into account")
            path_parts = file_path.split("/")
            self.transcriptions_path = "/".join(path_parts[:-1])
            print("transcriptions_path", self.transcriptions_path)
            transcription_name = path_parts[len(path_parts) - 1]
            print("transcription_name", transcription_name)
            self.transcription_name = transcription_name
            file_name = self.get_json_file_name()

        print("load", file_name)
        if os.path.exists(file_name):
            with open(file_name, "r", encoding='utf-8') as json_file:
                print("load", file_name)
                transcription_file_content_json = json.load(json_file)
                if TranscriptionStore.is_json_format_v_1_0(transcription_file_content_json):
                    self.file_format = transcription_file_content_json["FILE_FORMAT"]
                    json_transcription = transcription_file_content_json["transcription"]
                    self.set_transcription_data(self.format_json_transcription(json_transcription))
                    print("load.json_transcription", self.json_transcription)
                    self.set_parts_colors(transcription_file_content_json["parts_colors"])
                    print("load.json_parts_colors", self.json_parts_colors)
                    self.set_transcription_labels_data(transcription_file_content_json["transcription_labels"])
                    print("load.json_transcription_labels", self.json_transcription_labels)
                    self.set_labels_data(transcription_file_content_json["labels"])
                    print("load.json_labels", self.json_labels)
                else:  # todo add previous formats for retro compatibility
                    raise TranscriptionStoreException(f"The file {file_name} does not comply "
                                                      f"with format {TranscriptionStore.FILE_FORMAT}")
        else:
            raise FileExistsError(f"The file {file_name} does not exist")

    def save(self, transcription_file_name: str = None, transcription: dict = None, parts_colors: dict = None,
             labels: dict = None, transcription_labels: dict = None):
        """
        saves the transcription data into a json file
        """
        if transcription_file_name is None:
            transcription_file_name = self.get_json_file_name()
        if transcription is None:
            self.json_transcription = self.format_json_transcription(self.json_transcription)
            transcription = self.json_transcription
        else:
            transcription = self.format_json_transcription(transcription)
        if parts_colors is None:
            parts_colors = self.json_parts_colors
        else:
            self.json_parts_colors = parts_colors
        if labels is None:
            labels = self.json_labels
        else:
            self.json_labels = labels
        if transcription_labels is None:
            transcription_labels = self.json_transcription_labels
        else:
            self.json_transcription_labels = transcription_labels
        transcription_content = {"FILE_FORMAT": self.FILE_FORMAT,
                                 "transcription": transcription,
                                 "parts_colors": parts_colors,
                                 "transcription_labels": transcription_labels, "labels": labels
                                 }
        with open(transcription_file_name, "w", encoding='utf-8') as file:
            json.dump(transcription_content, file, indent=4, ensure_ascii=False)
        print(f"Saved to {transcription_file_name}")

    @staticmethod
    def is_file_format_v1_0(file_name: str) -> bool:
        """
        returns True if the file_name is compliant with FILE_FORMAT = "1.0"
        """
        if os.path.exists(file_name):
            with open(file_name, "r", encoding='utf-8') as file_desc:
                try:
                    json_file = json.load(file_desc)
                except JSONDecodeError as err:
                    return False
                return TranscriptionStore.is_json_format_v_1_0(json_file)
        else:
            raise FileNotFoundError(f"The file {file_name} does not exist")

    @staticmethod
    def is_json_format_v_1_0(json_file: dict) -> bool:
        if "FILE_FORMAT" not in json_file.keys():
            return False
        else:
            if json_file["FILE_FORMAT"] != "1.0":
                return False
        if "transcription" in json_file.keys():
            if not TranscriptionStore.is_transcription_format_ok(json_file["transcription"]):
                return False
        else:
            return False
        if "parts_colors" in json_file.keys():
            if not TranscriptionStore.is_parts_colors_format_ok(json_file["parts_colors"]):
                return False
        else:
            return False
        if "transcription_labels" in json_file.keys():
            if not TranscriptionStore.is_transcription_label_format_ok(json_file["transcription_labels"]):
                return False
        else:
            return False
        if "labels" in json_file.keys():
            if not TranscriptionStore.is_labels_format_ok(json_file["labels"]):
                return False
        else:
            return False
        return True

    def get_parts_colors(self) -> dict:
        if self.is_parts_colors_format_ok(self.json_parts_colors):
            res = deepcopy(self.json_parts_colors)
            return res
        else:
            raise ValueError(f"The internal data do not comply with format {self.FILE_FORMAT}")

    def set_parts_colors(self, data: dict):
        if self.is_parts_colors_format_ok(data):
            self.json_parts_colors = deepcopy(data)
        else:
            raise ValueError(f"The input data do not comply with format {self.FILE_FORMAT}")

    def get_transcription_data(self) -> dict:
        """
        returns a dict like {'0': ['ZER', 'TYU', 'IOP'], '1': ['QSD', 'FGH', 'JKL']}
        """
        if self.is_transcription_format_ok(self.json_transcription):
            res = deepcopy(self.json_transcription)
            return res
        else:
            raise ValueError(f"The internal data do not comply with format {self.FILE_FORMAT}")

    def set_transcription_data(self, data: dict):
        if self.is_transcription_format_ok(data):
            self.json_transcription = deepcopy(data)
        else:
            raise ValueError(f"The input data do not comply with format {self.FILE_FORMAT}")

    def set_labels_data(self, data: dict):
        if self.is_labels_format_ok(data):
            self.json_labels = deepcopy(data)
        else:
            raise ValueError(f"The input data do not comply with format {self.FILE_FORMAT}")

    def get_labels_data(self) -> dict:
        if self.is_labels_format_ok(self.json_labels):
            res = deepcopy(self.json_labels)
            return res
        else:
            raise ValueError(f"The input data do not comply with format {self.FILE_FORMAT}")

    def get_transcription_labels_data(self) -> dict:
        if self.is_transcription_label_format_ok(self.json_transcription_labels):
            res = deepcopy(self.json_labels)
            return res
        else:
            raise ValueError(f"The internal data do not comply with format {self.FILE_FORMAT}")

    def set_transcription_labels_data(self, data: dict):
        if self.is_transcription_label_format_ok(data):
            self.json_transcription_labels = deepcopy(data)
        else:
            raise ValueError(f"The input data do not comply with format {self.FILE_FORMAT}")

    @staticmethod
    def is_transcription_label_format_ok(transcription_labels: dict):
        for row_key in transcription_labels.keys():
            for beg_key in transcription_labels[row_key].keys():
                if not ("label" in transcription_labels[row_key][beg_key].keys()):
                    return False
                if not ("end" in transcription_labels[row_key][beg_key].keys()):
                    return False
                if not ("text" in transcription_labels[row_key][beg_key].keys()):
                    return False
        return True

    @staticmethod
    def is_transcription_format_ok(transcription: dict):
        for row_key in transcription.keys():
            if type(transcription[row_key]) == list:
                if not (len(transcription[row_key]) in [2, 3]):
                    print("2-3 items expected in transcription[row][]")
                    return False
            elif type(transcription[row_key]) == dict:
                return TranscriptionStore.is_transcription_format_ok(transcription[row_key])
            else:
                return False
        return True

    @staticmethod
    def is_labels_format_ok(labels: dict):
        for tag in labels.keys():
            if not ("color" in labels[tag].keys()):
                return False
            if not ("description" in labels[tag].keys()):
                return False
        return True

    @staticmethod
    def is_parts_colors_format_ok(parts_colors: dict):
        for tag_key in parts_colors.keys():
            if not ("color" in parts_colors[tag_key].keys()):
                return False
            if not ("description" in parts_colors[tag_key].keys()):
                return False
        return True

    @staticmethod
    def _is_it_a_row(json_part: dict):
        """
        return true if the json is a row of a transcription data
        ex: ["00:00:03", "non", ""]
        todo: add some control on lower parts
        """
        return type(json_part) == list

    @staticmethod
    def _is_it_a_part(json_part: dict):
        """
        return true if the json is a row of a transcription data
        ex: ["00:00:03", "non", ""]
        """
        return type(json_part) == dict

    @staticmethod
    def format_json_transcription(json_transcription: dict) -> dict:
        """
        recurse in json_transcription struct to handle parts
        json_transcription = {
                    "I001": ["00:00:02", "un je t'aime", ""],
                    "I002": ["00:00:03", "non", ""]
                    }
        """
        for row_key in json_transcription.keys():
            if TranscriptionStore._is_it_a_row(json_transcription[row_key]):
                if len(json_transcription[row_key]) == 2:
                    json_transcription[row_key].append("")  # adds a 3rd item to match tags
            elif TranscriptionStore._is_it_a_part(json_transcription[row_key]):
                TranscriptionStore.format_json_transcription(json_transcription[row_key])
            else:
                raise TranscriptionStoreException(f"The node {json_transcription[row_key]} found in transcription "
                                                  f"is not compliant with format {TranscriptionStore.FILE_FORMAT}")
        return json_transcription

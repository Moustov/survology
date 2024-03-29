from unittest import TestCase

from components.transcription_store import TranscriptionStore, TranscriptionStoreException


class TestTranscriptionStore(TestCase):
    def test_load_v1_0_empty(self):
        ts = TranscriptionStore("format v1.0")
        ts.load("tests/test_data/format v1.0.json", with_audio_file=False)

    def test_load_v1_0_with_parts(self):
        ts = TranscriptionStore("transcription_format_v1_0_with_parts")
        ts.load("tests/test_data/transcription_format_v1_0_with_parts.json", with_audio_file=False)
        self.assert_(ts.FILE_FORMAT == "1.0")
        self.assert_(len(ts.json_transcription.keys()) == 3)
        self.assert_(len(ts.json_parts_colors.keys()) == 1)
        self.assert_(ts.is_parts_colors_format_ok(ts.json_parts_colors))
        self.assert_(len(ts.json_transcription_labels.keys()) == 1)
        for tl in ts.json_transcription_labels.keys():
            self.assert_(len(ts.json_transcription_labels[tl].keys()) == 1)
            for line in ts.json_transcription_labels[tl].keys():
                self.assert_("label" in ts.json_transcription_labels[tl][line].keys())
                self.assert_("end" in ts.json_transcription_labels[tl][line].keys())
                self.assert_("text" in ts.json_transcription_labels[tl][line].keys())
        self.assert_(len(ts.json_labels.keys()) == 1)
        for tag in ts.json_labels.keys():
            self.assert_("color" in ts.json_labels[tag].keys())
            self.assert_("description" in ts.json_labels[tag].keys())


    def test_load_v1_0(self):
        ts = TranscriptionStore("transcription_format_v1_0")
        ts.load("tests/test_data/transcription_format_v1_0.json", with_audio_file=False)
        self.assert_(ts.FILE_FORMAT == "1.0")
        self.assert_(len(ts.json_transcription.keys()) == 4)
        self.assert_(len(ts.json_parts_colors.keys()) == 0)
        self.assert_(len(ts.json_transcription_labels.keys()) == 1)
        for tl in ts.json_transcription_labels.keys():
            self.assert_(len(ts.json_transcription_labels[tl].keys()) == 1)
            for line in ts.json_transcription_labels[tl].keys():
                self.assert_("label" in ts.json_transcription_labels[tl][line].keys())
                self.assert_("end" in ts.json_transcription_labels[tl][line].keys())
                self.assert_("text" in ts.json_transcription_labels[tl][line].keys())
        self.assert_(len(ts.json_labels.keys()) == 1)
        for tag in ts.json_labels.keys():
            self.assert_("color" in ts.json_labels[tag].keys())
            self.assert_("description" in ts.json_labels[tag].keys())

    def test_save_v1_0(self):
        init_ts = TranscriptionStore("transcription_format_v1_0")
        init_ts.load("tests/test_data/transcription_format_v1_0.json", with_audio_file=False)
        temp_file = "tmp/TranscriptionStore_testsave.json"
        init_ts.save(temp_file)
        self.assert_(TranscriptionStore.is_file_format_v1_0(temp_file))
        ts = TranscriptionStore("transcription_format_v1_0")
        ts.load(temp_file, with_audio_file=False)
        self.assert_(ts.FILE_FORMAT == "1.0")
        self.assert_(len(ts.json_transcription.keys()) == 4)
        self.assert_(len(ts.json_parts_colors.keys()) == 0)
        self.assert_(len(ts.json_transcription_labels.keys()) == 1)
        self.assert_(len(ts.json_labels.keys()) == 1)

    def test_is_format_v1_0(self):
        self.assert_(TranscriptionStore.is_file_format_v1_0("tests/test_data/transcription_format_v1_0.json"))
        self.assert_(not TranscriptionStore.is_file_format_v1_0("tests/test_data/old_version.json"))
        self.assert_(not TranscriptionStore.is_file_format_v1_0("README.md"))

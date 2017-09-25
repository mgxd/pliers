from os.path import join
from .utils import get_test_data_path
from pliers.converters import (get_converter,
                               VideoToAudioConverter, VideoToTextConverter,
                               TesseractConverter, WitTranscriptionConverter,
                               GoogleSpeechAPIConverter, IBMSpeechAPIConverter,
                               GoogleVisionAPITextConverter,
                               ComplexTextIterator)
from pliers.converters.image import ImageToTextConverter
from pliers.stimuli import (VideoStim, TextStim,
                            ComplexTextStim, AudioStim, ImageStim)
import numpy as np
import pytest


def test_video_to_audio_converter():
    filename = join(get_test_data_path(), 'video', 'small.mp4')
    video = VideoStim(filename, onset=4.2)
    conv = VideoToAudioConverter()
    audio = conv.transform(video)
    assert audio.history.source_class == 'VideoStim'
    assert audio.history.source_file == filename
    assert audio.onset == 4.2
    assert np.isclose(video.duration, audio.duration, 1e-2)


@pytest.mark.skipif("'WIT_AI_API_KEY' not in os.environ")
def test_witaiAPI_converter():
    audio_dir = join(get_test_data_path(), 'audio')
    stim = AudioStim(join(audio_dir, 'homer.wav'), onset=4.2)
    conv = WitTranscriptionConverter()
    out_stim = conv.transform(stim)
    assert type(out_stim) == ComplexTextStim
    first_word = next(w for w in out_stim)
    assert type(first_word) == TextStim
    assert first_word.onset == 4.2
    second_word = [w for w in out_stim][1]
    assert second_word.onset == 4.2
    text = [elem.text for elem in out_stim]
    assert 'thermodynamics' in text or 'obey' in text


@pytest.mark.skipif("'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ")
def test_googleAPI_converter():
    audio_dir = join(get_test_data_path(), 'audio')
    stim = AudioStim(join(audio_dir, 'homer.wav'))
    conv = GoogleSpeechAPIConverter()
    out_stim = conv.transform(stim)
    assert type(out_stim) == ComplexTextStim
    text = [elem.text for elem in out_stim]
    assert 'thermodynamics' in text or 'obey' in text


@pytest.mark.skipif("'IBM_USERNAME' not in os.environ or "
                    "'IBM_PASSWORD' not in os.environ")
def test_ibmAPI_converter():
    audio_dir = join(get_test_data_path(), 'audio')
    stim = AudioStim(join(audio_dir, 'homer.wav'), onset=4.2)
    conv = IBMSpeechAPIConverter()
    out_stim = conv.transform(stim)
    assert isinstance(out_stim, ComplexTextStim)
    first_word = next(w for w in out_stim)
    assert isinstance(first_word, TextStim)
    assert first_word.duration > 0
    assert first_word.onset is not None
    second_word = [w for w in out_stim][1]
    assert second_word.onset > 4.2
    num_words = len(out_stim.elements)
    full_text = [elem.text for elem in out_stim]
    assert 'thermodynamics' in full_text or 'obey' in full_text

    conv2 = IBMSpeechAPIConverter(resolution='phrases')
    out_stim = conv2.transform(stim)
    assert isinstance(out_stim, ComplexTextStim)
    first_phrase = next(w for w in out_stim)
    assert isinstance(first_phrase, TextStim)
    full_text = first_phrase.text
    assert len(full_text.split()) > 1
    assert 'thermodynamics' in full_text or 'obey' in full_text
    assert len(out_stim.elements) < num_words


def test_tesseract_converter():
    pytest.importorskip('pytesseract')
    image_dir = join(get_test_data_path(), 'image')
    stim = ImageStim(join(image_dir, 'button.jpg'), onset=4.2)
    conv = TesseractConverter()
    out_stim = conv.transform(stim)
    assert out_stim.name == 'text[Exit]'
    assert out_stim.history.source_class == 'ImageStim'
    assert out_stim.history.source_name == 'button.jpg'
    assert out_stim.onset == 4.2


@pytest.mark.skipif("'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ")
def test_google_vision_api_text_converter():
    conv = GoogleVisionAPITextConverter(num_retries=5)
    filename = join(get_test_data_path(), 'image', 'button.jpg')
    stim = ImageStim(filename)
    text = conv.transform(stim).text
    assert 'Exit' in text

    conv = GoogleVisionAPITextConverter(handle_annotations='concatenate')
    text = conv.transform(stim).text
    assert 'Exit' in text


def test_get_converter():
    conv = get_converter(ImageStim, TextStim)
    assert isinstance(conv, ImageToTextConverter)
    conv = get_converter(TextStim, ImageStim)
    assert conv is None


@pytest.mark.skipif("'WIT_AI_API_KEY' not in os.environ")
def test_multistep_converter():
    conv = VideoToTextConverter()
    filename = join(get_test_data_path(), 'video', 'obama_speech.mp4')
    stim = VideoStim(filename)
    text = conv.transform(stim)
    assert isinstance(text, ComplexTextStim)
    first_word = next(w for w in text)
    assert type(first_word) == TextStim


@pytest.mark.skipif("'WIT_AI_API_KEY' not in os.environ")
def test_stim_history_tracking():
    video = VideoStim(join(get_test_data_path(), 'video', 'obama_speech.mp4'))
    assert video.history is None
    conv = VideoToAudioConverter()
    stim = conv.transform(video)
    assert str(stim.history) == 'VideoStim->VideoToAudioConverter/AudioStim'
    conv = WitTranscriptionConverter()
    stim = conv.transform(stim)
    assert str(
        stim.history) == 'VideoStim->VideoToAudioConverter/AudioStim->WitTranscriptionConverter/ComplexTextStim'


def test_stim_iteration_converter():
    textfile = join(get_test_data_path(), 'text', 'scandal.txt')
    stim = ComplexTextStim(text=open(textfile).read().strip())
    words = ComplexTextIterator().transform(stim)
    assert len(words) == 231
    assert isinstance(words[1], TextStim)
    assert words[1].text == 'Sherlock'
    assert str(
        words[1].history) == 'ComplexTextStim->ComplexTextIterator/TextStim'

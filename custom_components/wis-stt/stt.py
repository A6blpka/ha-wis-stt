import aiohttp
import logging
from collections.abc import AsyncIterable
from webbrowser import get
from homeassistant.components import stt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WISSTT(hass, config_entry)])

class WISSTT(stt.SpeechToTextEntity):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.url: str = config_entry.data["url"]
        self.cert_validation: bool = config_entry.data["cert_validation"]
        self.model: str = config_entry.data["model"]
        self.detect_language: bool = config_entry.data["detect_language"]
        self.language: str = config_entry.data["language"]
        self.beam_size: int = config_entry.data["beam_size"]
        self.speaker: str = config_entry.data["speaker"]
        self.save_audio: bool = config_entry.data["save_audio"]

        self._attr_name = f"WIS STT {self.url} ({self.language})"
        self._attr_unique_id = f"{config_entry.entry_id[:7]}-stt"

    @property
    def supported_languages(self) -> list[str]:
        return [self.language]

    @property
    def supported_formats(self) -> list[stt.AudioFormats]:
        return [stt.AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        return [stt.AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        return [stt.AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        return [stt.AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[stt.AudioChannels]:
        return [stt.AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        _LOGGER.debug("process_audio_stream start")

        def session_creator(verify_ssl=None):
            if verify_ssl:
                return aiohttp.ClientSession()
            else:
                return aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))

        async def stream_reader(stream=None):
            async for chunk in stream:
                yield chunk

        async with session_creator(self.cert_validation) as session:
            session.headers.update({'x-audio-codec': 'pcm'})
            session.headers.update({'x-audio-channel': '1'})
            session.headers.update({'x-audio-bits': '16'})
            session.headers.update({'x-audio-sample-rate': '16000'})
            params = {'model': self.model, 'detect_language': str(self.detect_language),
                      'return_language': self.language, 'force_language': self.language,
                      'beam_size': self.beam_size, 'speaker':self.speaker, 'save_audio': str(self.save_audio)}
            async with session.post(self.url, params=params, data=stream_reader(stream=stream)) as resp:
                text = await resp.json(content_type=None)
        
        _LOGGER.info(f"process_audio_stream end: {text}")

        text = text["text"]

        return stt.SpeechResult(text, stt.SpeechResultState.SUCCESS)

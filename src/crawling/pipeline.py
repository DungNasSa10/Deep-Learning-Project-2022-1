import os
from utils.tools import get_voices_and_urls
from crawling.mixin import StepMixin
from crawling.downloader import Downloader
from crawling.vad_processor import VADProcessor
from crawling.outlier_remover import OutlierRemover
from utils.tools import is_gg_drive_url


class Pipeline(StepMixin):
    def __init__(self) -> None:
        super().__init__() 

        self.downloader = Downloader()
        self.vad_processor = VADProcessor()
        self.outlier_remover = OutlierRemover()

    def run(self, filepath_or_url: str, save_dir: str='./data/wavs', sampling_rate: int=16000, remove_mp3: bool=True, ):
        """
        Args:
            filepath: str \
                csv voide file path
            save_dir: str \
                directory to save .wav file
            remove_mp3: 
                remove old mp3 files or not
            sampling_rate: int, default = 16000 \
                sampling rate of .wav file
        """
        self.logger.info("Start full process")

        voice_and_urls = get_voices_and_urls(filepath_or_url)
        fn = os.path.basename(filepath_or_url)
        removal = '\/%^&$?*#'
        fn = "".join([t for t in fn if t not in removal])
        fn = os.path.splitext(fn)[0] + "-downloaded-urls.txt"
        fn = os.path.join("output", "ckpt", fn)
        
        if os.path.exists(fn) is False:

            if os.path.exists(os.path.dirname(fn)) is False:
                self.logger.info(f"Create directory: {os.path.dirname(fn)}")
                os.makedirs(os.path.dirname(fn))

            self.logger.info(f"Create urls check list at file: {fn}")
            open(fn, 'w', encoding='utf-8').close()
        
        def get_processed_urls():
            f = open(fn, 'r', encoding='utf-8')
            urls = f.read().split()
            f.close()
            return urls

        def insert_url(url):
            f = open(fn, 'a', encoding='utf-8')
            f.write(url + '\n')
            f.close()

        for voice, urls in voice_and_urls:
            self.logger.info("Start downloading videos of voice: " + voice)
            
            directory = os.path.join(save_dir, voice)
            if os.path.exists(directory) is False:
                self.logger.warning("Create directory " + directory)
                os.makedirs(directory)
            
            for url in urls:
                if url in get_processed_urls():
                    self.logger.warning(f"Skip url {url} because it has finished the process")
                    continue

                wav_path = self.downloader.run(url, save_dir=directory, sampling_rate=sampling_rate, remove_mp3=remove_mp3)
                wav_dir = self.vad_processor.run(wav_path, sampling_rate=sampling_rate)
                self.outlier_remover.run(wav_dir, sampling_rate=sampling_rate)

                insert_url(url)
            self.logger.info("Finish processing for voice: " + voice)

        self.logger.info("Finish full process")
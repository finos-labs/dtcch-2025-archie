import json
import boto3
from botocore.exceptions import ClientError
from common.s3_interface import S3Interface
from contextlib import closing
import cv2
import os
import logging
from moviepy import VideoFileClip, AudioFileClip

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AsyncPolly():
    def __init__(self,polly, config):
        self.polly = polly
        self.config = config
        self.media_abs_path = os.path.abspath('./common/media')


    def set_voice_id(self, voice_id):
        self.voice_id = voice_id
        self.engine = self.get_poly_voice_engine(voice_id)

    def set_llm_answer_text(self, llm_answer_text):
        self.llm_answer_text = llm_answer_text
    
    def set_avatar_name(self, avatar_name):
        self.avatar_name = avatar_name


    def get_image_visemes(self, avatar):
        return {
            "p": {"name": f"{self.media_abs_path}/{self.avatar_name}/b-m-p.png"},
            "t": {"name": f"{self.media_abs_path}/{self.avatar_name}/c-d-g-k-n-s-t-x-y-z.png"},
            "S": {"name": f"{self.media_abs_path}/{self.avatar_name}/ch-j-sh.png"},
            "T": {"name": f"{self.media_abs_path}/{self.avatar_name}/th.png"},
            "f": {"name": f"{self.media_abs_path}/{self.avatar_name}/f-v.png"},
            "k": {"name": f"{self.media_abs_path}/{self.avatar_name}/c-d-g-k-n-s-t-x-y-z.png"},
            "i": {"name": f"{self.media_abs_path}/{self.avatar_name}/a-e-i.png"},
            "l": {"name": f"{self.media_abs_path}/{self.avatar_name}/l.png"},
            "r": {"name": f"{self.media_abs_path}/{self.avatar_name}/r.png"},
            "s": {"name": f"{self.media_abs_path}/{self.avatar_name}/c-d-g-k-n-s-t-x-y-z.png"},
            "u": {"name": f"{self.media_abs_path}/{self.avatar_name}/q-w.png"},
            "@": {"name": f"{self.media_abs_path}/{self.avatar_name}/u.png"},
            "a": {"name": f"{self.media_abs_path}/{self.avatar_name}/a-e-i.png"},
            "e": {"name": f"{self.media_abs_path}/{self.avatar_name}/a-e-i.png"},
            "E": {"name": f"{self.media_abs_path}/{self.avatar_name}/u.png"},
            "o": {"name": f"{self.media_abs_path}/{self.avatar_name}/o.png"},
            "O": {"name": f"{self.media_abs_path}/{self.avatar_name}/u.png"},
            "sil": {"name": f"{self.media_abs_path}/{self.avatar_name}/b-m-p.png"}
        }
		


    async def generate_synch_polly_audio_stream(self):
        # Call the Polly API (synchronously)
        response = self.polly.synthesize_speech(
            Text=self.llm_answer_text,
            OutputFormat="mp3",
            VoiceId=self.voice_id,
            Engine=self.engine  
        )

        # Get the AudioStream from the response
        audio_stream: StreamingBody = response["AudioStream"]

        # Read and stream audio in chunks
        chunk_size = 1024  
        while chunk := audio_stream.read(chunk_size):
            yield chunk

        # Close the audio stream
        audio_stream.close()
      
    
    async def generate_polly_audio_file(self, file_name):
        mp3_file_name = f"audio_{file_name}.mp3"
        mp3_file_path = f"./{mp3_file_name}"
        response = self.polly.synthesize_speech(Text=self.llm_answer_text,
                                OutputFormat="mp3",
                                VoiceId=self.voice_id,
                                Engine=self.engine)
        
        with closing(response["AudioStream"]) as stream:
            with open(mp3_file_path, "wb") as file:
                file.write(stream.read())

        self.mp3_file_path = mp3_file_path

        yield mp3_file_path

    async def get_polly_viseme(self):
        #generative engine does not support visime
        response = self.polly.synthesize_speech(
            Text=self.llm_answer_text, 
            VoiceId=self.voice_id,
            Engine='neural',
            OutputFormat="json", 
            SpeechMarkTypes=["viseme"])
        visemes = [
            json.loads(viseme)
            for viseme in response["AudioStream"].read().decode().split()
            if viseme
        ]
        yield visemes 


    def get_poly_voices(self):
        response = self.polly.describe_voices()
        #print(response)
        voice_ids = [{"voice_id": item['Id'],"language_name": item['LanguageName'], "gender": item['Gender']} for item in response['Voices'] if item['LanguageCode'].startswith('en')]
        return voice_ids

    def get_poly_voice_engines(self, voice_id):
        #response = self.polly.describe_voices()
        print(response)
        engines = [item['SupportedEngines'] for item in response['Voices'] if (item['LanguageCode'].startswith('en')) and (item['Id'] == voice_id)]
        return engines[0]

    def get_poly_voice_engine(self, voice_id):
        response = self.polly.describe_voices()
        #print(response)
        engines = [item['SupportedEngines'] for item in response['Voices'] if (item['LanguageCode'].startswith('en')) and (item['Id'] == voice_id)]
        logger.info(f"get_poly_voice_engine engines[0] {engines[0][0]}")
        return engines[0][0]

    async def generate_viseme_frames(self, visemes):
        # Convert time (ms) to frames
        fps = 24  # Adjust based on animation speed
        frame_timings = [(int(viseme["time"] / (1000 / fps)), viseme["value"]) for viseme in visemes]

        print(frame_timings) 
        yield frame_timings

    async def generate_lipsynch_frames(self, frame_timings):
        logger.info(f"curent directory *********** {os.getcwd()}")
        file_path = f'{self.media_abs_path}/{self.avatar_name}/avatar.png'
        logger.info(f"{file_path} exists ---> {os.path.exists(file_path)}")
        logger.info(f"Absolute path for ./common/media:------> {os.path.abspath('./common/media')}")
        # Load avatar image
        avatar = cv2.imread(f"{self.media_abs_path}/{self.avatar_name}/avatar.png")
        frame_folder = "frames"
        os.makedirs(frame_folder, exist_ok=True)

        # Get video dimensions
        height, width, _ = avatar.shape
        viseme_to_mouth = self.get_image_visemes(self.avatar_name)

        # Generate frames based on viseme timings
        for i, (frame_num, viseme) in enumerate(frame_timings):
            frame = avatar.copy()
            
            # Load the corresponding mouth shape

            mouth_shape = viseme_to_mouth.get(viseme, "{self.media_abs_path}/{self.avatar_name}/b-m-p.png")
            logger.info(f"mouth_shape --------> {mouth_shape}")
            mouth = cv2.imread(mouth_shape['name'])

            # Overlay mouth on avatar (adjust coordinates)
            #Define mouth placement region
            y1, y2 = 100, 145  # Vertical range (height = 50)
            x1, x2 = 150, 208  # Horizontal range (width = 60)
            #(45,58,3) into shape (50,60,3)
            target_height = y2 - y1  # 50
            target_width = x2 - x1   # 60
            #mouth_resized = cv2.resize(mouth, (target_width, target_height))
            frame[y1:y2, x1:x2] = mouth

            # Save frame
            cv2.imwrite(f"{frame_folder}/frame_{i:04d}.png", frame)

        print("Frames generated.")

    async def generate_video_from_frames(self,file_name):
        mp4_file_name = f"video_{file_name}_temp.mp4"
        mp4_file_path = f"./{mp4_file_name}"
        frame_folder = "frames"
        fps = 24

        frame_files = sorted(os.listdir(frame_folder))

        # Get first frame dimensions
        frame = cv2.imread(os.path.join(frame_folder, frame_files[0]))
        height, width, _ = frame.shape

        # Create video writer
        video_writer = cv2.VideoWriter(mp4_file_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

        # Write frames to video
        for frame_file in frame_files:
            frame = cv2.imread(os.path.join(frame_folder, frame_file))
            video_writer.write(frame)

        video_writer.release()
        print("Video created.")
        yield mp4_file_path

    async def combine_mp3_mp4(self, file_name):
        mp3_file_name = f"audio_{file_name}.mp3"
        mp3_file_path = f"./{mp3_file_name}"
        mp4_file_name = f"video_{file_name}_temp.mp4"
        mp4_file_path = f"./{mp4_file_name}"
        mp4_final_file_path = mp4_file_path.replace('_temp','')


        # Load video and audio
        video = VideoFileClip(mp4_file_path)
        audio = AudioFileClip(mp3_file_path)

        # Set the audio of the video
        video = video.set_audio(audio)

        # Export final video
        await asyncio.to_thread(video.write_videofile, mp4_final_file_path, codec="libx264", audio_codec="aac")
        print("Final video created with audio.")
        yield mp4_final_file_path
        

    async def generate_video(self, file_name, ):
        """Asynchronously generate the final MP4 video with lipsync and audio."""
        print("Starting final video generation...")

        # Generate the MP3 audio file
        async for mp3_file_path in self.generate_polly_audio_file(file_name):
            print(f"Audio saved: {mp3_file_path}")

        # Get viseme timings from Polly
        async for visemes in self.get_polly_viseme():
            async for frame_timings in self.generate_viseme_frames(visemes):
                # Generate lipsync frames
                await self.generate_lipsynch_frames(frame_timings)


        # Generate video from frames
        video_path = await self.generate_video_from_frames(file_name)

        # Combine MP3 and MP4 into a final MP4 file
        final_video_path = await self.combine_mp3_mp4(file_name)

        print(f"Final video created: {final_video_path}")
        yield final_video_path


    def get_avatars(self):
        return [{"avatar_name": entry.name, "avatar_image": f"{self.media_abs_path}/{entry.name}/avatar.png"} for entry in os.scandir("{self.media_abs_path}") if entry.is_dir()]

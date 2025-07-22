import asyncio
import logging
import os
import sys
import traceback
import subprocess
import tempfile
import shutil
import base64
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from neonize.aioze.client import ClientFactory, NewAClient
from neonize.events import (
    ConnectedEv,
    MessageEv,
)
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message
from neonize.utils import log

# Tambahkan import dari thundra_io
try:
    from thundra_io.utils import get_message_type, get_user_id
    from thundra_io.types import MediaMessageType
    from thundra_io.storage.file import File
    THUNDRA_AVAILABLE = True
except ImportError:
    THUNDRA_AVAILABLE = False
    log.warning("thundra_io not available, some features may be limited")

sys.path.insert(0, os.getcwd())

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log.setLevel(logging.DEBUG)

# AI Configuration
GEMINI_API_KEY = "<APIKEY-GEMINI>"
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_CONTENT_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

# Setup client
client_factory = ClientFactory("db.sqlite3")
os.makedirs("downloads", exist_ok=True)
os.makedirs("temp_media", exist_ok=True)

# Load existing sessions
sessions = client_factory.get_all_devices()
for device in sessions:
    client_factory.new_client(device.JID)

class AIProcessor:
    """AI processing untuk transcription dan summarization"""
    
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_api_key}"
    
    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Transcribe audio menggunakan Gemini AI"""
        try:
            log.info(f"Transcribing audio, type: {mime_type}, size: {len(audio_bytes)} bytes")
            
            # Encode audio as base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": audio_b64
                                }
                            },
                            {
                                "text": "Please transcribe this audio to text. Provide the transcription in the same language as the audio. If the audio is in Indonesian, respond in Indonesian. If it's in English, respond in English. Just provide the transcription without additional commentary."
                            }
                        ]
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.gemini_url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        response_json = json.loads(response_text)
                        try:
                            transcription = response_json["candidates"][0]["content"]["parts"][0]["text"]
                            return {"success": True, "transcription": transcription}
                        except (KeyError, IndexError) as e:
                            log.error(f"Error parsing transcription response: {e}")
                            return {"success": False, "error": "Failed to parse AI response"}
                    else:
                        log.error(f"Gemini API error for transcription: {response_text}")
                        return {"success": False, "error": f"API error: Status {response.status}"}
        except Exception as e:
            log.error(f"Error in transcribe_audio: {e}")
            return {"success": False, "error": str(e)}
    
    async def summarize_content(self, content: str, content_type: str = "text") -> Dict[str, Any]:
        """Summarize content menggunakan Gemini AI"""
        try:
            log.info(f"Summarizing {content_type} content, length: {len(content)} chars")
            
            # Create context-aware prompt
            if content_type == "transcription":
                prompt = f"""Please provide a concise summary of this audio transcription in Indonesian. 
                
Transcription:
{content}

Please provide:
1. 📝 **Ringkasan Singkat** (2-3 kalimat utama)
2. 🎯 **Poin-poin Penting** (bullet points)
3. 🏷️ **Kategori** (musik, tutorial, berita, podcast, dll)

Format your response in Indonesian."""
            else:
                prompt = f"""Please provide a summary of this content in Indonesian:

{content}

Please make it concise and informative."""
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.gemini_url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        response_json = json.loads(response_text)
                        try:
                            summary = response_json["candidates"][0]["content"]["parts"][0]["text"]
                            return {"success": True, "summary": summary}
                        except (KeyError, IndexError) as e:
                            log.error(f"Error parsing summary response: {e}")
                            return {"success": False, "error": "Failed to parse AI response"}
                    else:
                        log.error(f"Gemini API error for summary: {response_text}")
                        return {"success": False, "error": f"API error: Status {response.status}"}
        except Exception as e:
            log.error(f"Error in summarize_content: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_media(self, media_bytes: bytes, mime_type: str, prompt: str = None) -> Dict[str, Any]:
        """Analyze media menggunakan Gemini AI"""
        try:
            log.info(f"Analyzing media, type: {mime_type}, size: {len(media_bytes)} bytes")
            
            media_b64 = base64.b64encode(media_bytes).decode('utf-8')
            
            parts = [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": media_b64
                    }
                }
            ]
            
            if prompt:
                parts.append({"text": prompt})
            else:
                if "image" in mime_type:
                    parts.append({"text": "Describe this image in detail. What do you see? Respond in Indonesian."})
                elif "video" in mime_type:
                    parts.append({"text": "Describe this video. What's happening? Respond in Indonesian."})
                elif "audio" in mime_type:
                    parts.append({"text": "Transcribe and summarize this audio content. Respond in Indonesian."})
            
            payload = {
                "contents": [
                    {
                        "parts": parts
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.gemini_url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        response_json = json.loads(response_text)
                        try:
                            analysis = response_json["candidates"][0]["content"]["parts"][0]["text"]
                            return {"success": True, "analysis": analysis}
                        except (KeyError, IndexError) as e:
                            log.error(f"Error parsing analysis response: {e}")
                            return {"success": False, "error": "Failed to parse AI response"}
                    else:
                        log.error(f"Gemini API error for analysis: {response_text}")
                        return {"success": False, "error": f"API error: Status {response.status}"}
        except Exception as e:
            log.error(f"Error in analyze_media: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_for_youtube(self, media_bytes: bytes, mime_type: str, media_type: str) -> Dict[str, Any]:
        """Analyze media untuk YouTube content creation"""
        try:
            log.info(f"Analyzing {media_type} for YouTube content, type: {mime_type}, size: {len(media_bytes)} bytes")
            
            media_b64 = base64.b64encode(media_bytes).decode('utf-8')
            
            youtube_prompt = f"""Analisis {media_type} ini dan buatkan:

JUDUL YOUTUBE (3 pilihan terbaik):
- Maksimal 60 karakter, menarik, SEO-friendly
- [berikan 3 variasi judul]

DESKRIPSI:
- Paragraf pembuka yang hook (2-3 kalimat)
- Ringkasan isi {media_type}
- Call-to-action
- Timestamps jika perlu

HASHTAG (15 hashtag):
- Mix antara viral, niche, dan long-tail
- Urutkan dari umum ke spesifik

BONUS:
- Target audience utama
- Waktu upload terbaik
- Ide thumbnail

Fokus pada konten yang benar-benar ada di {media_type}. Buat yang viral tapi tetap relevan!

Respond dalam bahasa Indonesia dengan format yang rapi dan mudah dibaca."""
            
            parts = [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": media_b64
                    }
                },
                {
                    "text": youtube_prompt
                }
            ]
            
            payload = {
                "contents": [
                    {
                        "parts": parts
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.gemini_url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        response_json = json.loads(response_text)
                        try:
                            youtube_analysis = response_json["candidates"][0]["content"]["parts"][0]["text"]
                            return {"success": True, "youtube_analysis": youtube_analysis}
                        except (KeyError, IndexError) as e:
                            log.error(f"Error parsing YouTube analysis response: {e}")
                            return {"success": False, "error": "Failed to parse AI response"}
                    else:
                        log.error(f"Gemini API error for YouTube analysis: {response_text}")
                        return {"success": False, "error": f"API error: Status {response.status}"}
        except Exception as e:
            log.error(f"Error in analyze_for_youtube: {e}")
            return {"success": False, "error": str(e)}

class MediaDownloader:
    """Universal media downloader dengan AI features"""
    
    def __init__(self, ai_processor: AIProcessor):
        self.download_dir = "downloads"
        self.ai_processor = ai_processor
        
        # Platform yang didukung yt-dlp
        self.popular_platforms = {
            "youtube.com": "YouTube", "youtu.be": "YouTube",
            "tiktok.com": "TikTok", "vt.tiktok.com": "TikTok", "vm.tiktok.com": "TikTok",
            "instagram.com": "Instagram", "facebook.com": "Facebook", "fb.watch": "Facebook",
            "twitter.com": "Twitter", "x.com": "Twitter", "t.co": "Twitter",
            "vimeo.com": "Vimeo", "dailymotion.com": "Dailymotion",
            "twitch.tv": "Twitch", "reddit.com": "Reddit",
            "soundcloud.com": "SoundCloud", "spotify.com": "Spotify",
        }
    
    def get_platform_name(self, url: str) -> str:
        """Detect platform from URL"""
        url_lower = url.lower()
        for domain, platform in self.popular_platforms.items():
            if domain in url_lower:
                return platform
        return "Unknown Platform"
    
    async def get_info(self, url: str) -> Dict[str, Any]:
        """Get media information - FIXED VERSION"""
        try:
            log.info(f"Getting info for: {url}")
            
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-warnings",
                "--no-playlist",
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                stdout_text = stdout.decode().strip()
                
                # PERBAIKAN: Cek apakah stdout kosong
                if not stdout_text:
                    log.error("yt-dlp returned empty output")
                    return {"success": False, "error": "No information available for this URL"}
                
                try:
                    # PERBAIKAN: Handle multiple JSON objects (playlist case)
                    lines = stdout_text.split('\n')
                    info = None
                    
                    for line in lines:
                        if line.strip():
                            try:
                                info = json.loads(line)
                                break  # Use the first valid JSON
                            except json.JSONDecodeError as json_error:
                                log.warning(f"Failed to parse JSON line: {json_error}")
                                continue
                    
                    # PERBAIKAN: Cek apakah JSON berhasil di-parse
                    if info is None:
                        log.error("Failed to parse any JSON from yt-dlp output")
                        return {"success": False, "error": "Failed to parse media information"}
                    
                    # PERBAIKAN: Provide default values untuk missing keys
                    return {
                        "success": True,
                        "title": info.get("title", "Unknown Title")[:80],
                        "uploader": info.get("uploader", "Unknown")[:30],
                        "duration": info.get("duration", 0) or 0,
                        "view_count": info.get("view_count", 0) or 0,
                        "platform": self.get_platform_name(url),
                        "thumbnail": info.get("thumbnail", ""),
                        "description": (info.get("description") or "")[:150],
                        "webpage_url": info.get("webpage_url") or url
                    }
                    
                except json.JSONDecodeError as json_error:
                    log.error(f"JSON decode error: {json_error}")
                    log.error(f"Raw output: {stdout_text[:500]}")
                    return {"success": False, "error": f"JSON parse error: {str(json_error)}"}
                    
            else:
                error_msg = stderr.decode()
                log.error(f"yt-dlp info error: {error_msg}")
                
                # PERBAIKAN: Provide more specific error messages
                if "unsupported url" in error_msg.lower():
                    return {"success": False, "error": "URL not supported by yt-dlp"}
                elif "video unavailable" in error_msg.lower():
                    return {"success": False, "error": "Video is unavailable or private"}
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    return {"success": False, "error": "Network connection error"}
                else:
                    return {"success": False, "error": error_msg[:200]}
                
        except Exception as e:
            log.error(f"Error getting info: {e}")
            log.error(traceback.format_exc())
            return {"success": False, "error": f"Exception: {str(e)}"}
    
    async def download(self, url: str, media_type: str = "audio", quality: str = "best", chat_id: str = None) -> Dict[str, Any]:
        """Universal download method dengan AI processing - IMPROVED ERROR HANDLING"""
        try:
            log.info(f"Downloading {media_type} from: {url}")
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_chat = chat_id.replace("@", "").replace(".", "") if chat_id else "unknown"
            
            if media_type == "audio":
                output_template = f"{self.download_dir}/audio_{safe_chat}_{timestamp}.%(ext)s"
                cmd = [
                    "yt-dlp",
                    "-x",  # Extract audio
                    "--audio-format", "mp3",
                    "--audio-quality", "0",  # Best quality
                    "--no-warnings",
                    "--no-playlist",
                    "--embed-metadata",
                    "-o", output_template,
                    url
                ]
                expected_ext = ".mp3"
                
            else:  # video
                output_template = f"{self.download_dir}/video_{safe_chat}_{timestamp}.%(ext)s"
                
                # Quality mapping
                quality_formats = {
                    "worst": "worst",
                    "480p": "best[height<=480]",
                    "720p": "best[height<=720]", 
                    "1080p": "best[height<=1080]",
                    "best": "best"
                }
                
                format_selector = quality_formats.get(quality, "best[height<=720]")
                
                cmd = [
                    "yt-dlp",
                    "-f", format_selector,
                    "--no-warnings",
                    "--no-playlist",
                    "--embed-metadata",
                    "-o", output_template,
                    url
                ]
                expected_ext = ".mp4"
            
            log.info(f"Running: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Find downloaded file
                if media_type == "audio":
                    file_path = output_template.replace(".%(ext)s", ".mp3")
                else:
                    # Check for various video formats
                    possible_exts = [".mp4", ".webm", ".mkv", ".avi", ".mov"]
                    file_path = None
                    for ext in possible_exts:
                        test_path = output_template.replace(".%(ext)s", ext)
                        if os.path.exists(test_path):
                            file_path = test_path
                            break
                
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    file_ext = os.path.splitext(file_path)[1][1:]  # Remove dot
                    
                    log.info(f"{media_type.title()} download successful: {file_path} ({file_size} bytes)")
                    
                    return {
                        "success": True,
                        "file_path": file_path,
                        "file_size": file_size,
                        "format": file_ext,
                        "type": media_type
                    }
                else:
                    log.error("Downloaded file not found")
                    return {"success": False, "error": "Downloaded file not found"}
            else:
                error_msg = stderr.decode()
                log.error(f"yt-dlp error: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            log.error(f"Error in download: {e}")
            log.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    async def download_with_ai(self, url: str, ai_features: List[str] = None, quality: str = "720p", chat_id: str = None) -> Dict[str, Any]:
        """Download dengan AI processing (transcription, summary, analysis) - IMPROVED"""
        try:
            platform = self.get_platform_name(url)
            ai_features = ai_features or []
            
            # Get info first - IMPROVED ERROR HANDLING
            log.info("Getting media info...")
            info_result = await self.get_info(url)
            if not info_result["success"]:
                log.error(f"Failed to get info: {info_result['error']}")
                return {"success": False, "error": f"Failed to get media info: {info_result['error']}"}
            
            results = {
                "success": True,
                "info": info_result,
                "ai_results": {}
            }
            
            # Download audio for transcription/summary
            if "transcribe" in ai_features or "summary" in ai_features:
                log.info("Downloading audio for AI processing...")
                audio_result = await self.download(url, "audio", "best", chat_id)
                if audio_result["success"]:
                    try:
                        # Read audio file
                        with open(audio_result["file_path"], "rb") as f:
                            audio_bytes = f.read()
                        
                        # Transcription
                        if "transcribe" in ai_features:
                            log.info("Starting transcription...")
                            transcribe_result = await self.ai_processor.transcribe_audio(audio_bytes, "audio/mp3")
                            results["ai_results"]["transcription"] = transcribe_result
                            
                            # Summary dari transcription
                            if "summary" in ai_features and transcribe_result.get("success"):
                                log.info("Creating summary from transcription...")
                                summary_result = await self.ai_processor.summarize_content(
                                    transcribe_result["transcription"], "transcription"
                                )
                                results["ai_results"]["summary"] = summary_result
                        
                        # Cleanup audio file after AI processing
                        if os.path.exists(audio_result["file_path"]):
                            os.remove(audio_result["file_path"])
                            
                    except Exception as audio_error:
                        log.error(f"Error processing audio: {audio_error}")
                        results["ai_results"]["transcription"] = {"success": False, "error": f"Audio processing error: {str(audio_error)}"}
                        # Cleanup on error
                        if os.path.exists(audio_result["file_path"]):
                            os.remove(audio_result["file_path"])
                else:
                    results["ai_results"]["transcription"] = {"success": False, "error": f"Failed to download audio: {audio_result.get('error', 'Unknown error')}"}
            
            # Download video for analysis
            if "analyze" in ai_features:
                log.info("Downloading video for analysis...")
                video_result = await self.download(url, "video", quality, chat_id)
                if video_result["success"]:
                    try:
                        # Read video file (sample)
                        with open(video_result["file_path"], "rb") as f:
                            # Read first 5MB for analysis to avoid huge files
                            video_bytes = f.read(5 * 1024 * 1024)
                        
                        log.info("Starting video analysis...")
                        analysis_result = await self.ai_processor.analyze_media(
                            video_bytes, "video/mp4", "Analyze this video content"
                        )
                        results["ai_results"]["analysis"] = analysis_result
                        results["video_file"] = video_result
                        
                    except Exception as video_error:
                        log.error(f"Error processing video: {video_error}")
                        results["ai_results"]["analysis"] = {"success": False, "error": f"Video processing error: {str(video_error)}"}
                        # Cleanup on error
                        if os.path.exists(video_result["file_path"]):
                            os.remove(video_result["file_path"])
                else:
                    results["ai_results"]["analysis"] = {"success": False, "error": f"Failed to download video: {video_result.get('error', 'Unknown error')}"}
            
            return results
            
        except Exception as e:
            log.error(f"Error in download_with_ai: {e}")
            log.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

    async def download_for_youtube_analysis(self, url: str, media_type: str = "video", chat_id: str = None) -> Dict[str, Any]:
        """Download media khusus untuk analisis YouTube dengan kualitas worst - IMPROVED"""
        try:
            platform = self.get_platform_name(url)
            log.info(f"Downloading {media_type} for YouTube analysis from {platform}")
            
            # Get info first - IMPROVED ERROR HANDLING  
            info_result = await self.get_info(url)
            if not info_result["success"]:
                return {"success": False, "error": f"Failed to get media info: {info_result['error']}"}
            
            # Download dengan kualitas worst untuk menghemat bandwidth
            download_result = await self.download(url, media_type, "worst", chat_id)
            
            if download_result["success"]:
                try:
                    # Read file for AI analysis
                    with open(download_result["file_path"], "rb") as f:
                        if media_type == "video":
                            # Read first 10MB for video analysis
                            media_bytes = f.read(10 * 1024 * 1024)
                            mime_type = "video/mp4"
                        else:  # audio
                            # Read entire audio file (should be smaller with worst quality)
                            media_bytes = f.read()
                            mime_type = "audio/mp3"
                    
                    # YouTube analysis
                    youtube_result = await self.ai_processor.analyze_for_youtube(
                        media_bytes, mime_type, media_type
                    )
                    
                    # Cleanup downloaded file
                    if os.path.exists(download_result["file_path"]):
                        os.remove(download_result["file_path"])
                    
                    return {
                        "success": True,
                        "info": info_result,
                        "youtube_analysis": youtube_result
                    }
                    
                except Exception as analysis_error:
                    log.error(f"Error in YouTube analysis: {analysis_error}")
                    # Cleanup on error
                    if os.path.exists(download_result["file_path"]):
                        os.remove(download_result["file_path"])
                    return {"success": False, "error": f"YouTube analysis error: {str(analysis_error)}"}
            else:
                return {"success": False, "error": f"Download failed: {download_result.get('error', 'Unknown error')}"}
                
        except Exception as e:
            log.error(f"Error in download_for_youtube_analysis: {e}")
            log.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        log.info(f"Cleaned up: {filename}")
        except Exception as e:
            log.error(f"Cleanup error: {e}")

# Helper functions for quoted message handling
async def get_quoted_message_info(message):
    """Get quoted message info with balanced detection"""
    has_quoted = False
    quoted_message = None
    quoted_type = None
    
    try:
        if (hasattr(message.Message, 'extendedTextMessage') and 
            hasattr(message.Message.extendedTextMessage, 'contextInfo') and
            hasattr(message.Message.extendedTextMessage.contextInfo, 'quotedMessage')):
            
            quoted_message = message.Message.extendedTextMessage.contextInfo.quotedMessage
            has_quoted = True
            
            log.info("Quoted message detected, analyzing type...")
            
            # Method 1: Try thundra_io detection first
            if THUNDRA_AVAILABLE:
                try:
                    msg_type = get_message_type(quoted_message)
                    if isinstance(msg_type, MediaMessageType):
                        quoted_type = msg_type.__class__.__name__.lower().replace('message', '')
                        log.info(f"thundra_io detected type: {quoted_type}")
                        
                        # Cross-validate with manual detection
                        manual_type = None
                        # Check all types explicitly
                        if hasattr(quoted_message, 'audioMessage') and quoted_message.audioMessage and quoted_message.audioMessage.ByteSize() > 0:
                            manual_type = "audio"
                        elif hasattr(quoted_message, 'videoMessage') and quoted_message.videoMessage and quoted_message.videoMessage.ByteSize() > 0:
                            manual_type = "video"
                        elif hasattr(quoted_message, 'imageMessage') and quoted_message.imageMessage and quoted_message.imageMessage.ByteSize() > 0:
                            manual_type = "image"
                        elif hasattr(quoted_message, 'documentMessage') and quoted_message.documentMessage and quoted_message.documentMessage.ByteSize() > 0:
                            manual_type = "document"
                        
                        if manual_type and manual_type != quoted_type:
                            log.warning(f"thundra_io vs manual mismatch: {quoted_type} vs {manual_type}")
                            quoted_type = manual_type  # Trust manual detection
                            log.info(f"Using manual detection: {quoted_type}")
                        
                        log.info(f"Final thundra_io result: {quoted_type}")
                        return has_quoted, quoted_message, quoted_type
                        
                except Exception as e:
                    log.error(f"Error using thundra_io for detection: {e}")
            
            # Method 2: Manual detection - check all types without priority bias
            log.info("Using manual detection method...")
            detected_types = []
            
            # Check all possible types and log what we find
            if hasattr(quoted_message, 'audioMessage') and quoted_message.audioMessage and quoted_message.audioMessage.ByteSize() > 0:
                detected_types.append("audio")
                audio_msg = quoted_message.audioMessage
                is_ptt = getattr(audio_msg, 'ptt', False)
                mime_type = getattr(audio_msg, 'mimetype', 'unknown')
                log.info(f"Found AUDIO message - PTT: {is_ptt}, mime: {mime_type}")
                
            if hasattr(quoted_message, 'videoMessage') and quoted_message.videoMessage and quoted_message.videoMessage.ByteSize() > 0:
                detected_types.append("video")
                video_msg = quoted_message.videoMessage
                mime_type = getattr(video_msg, 'mimetype', 'unknown')
                log.info(f"Found VIDEO message - mime: {mime_type}")
                
            if hasattr(quoted_message, 'imageMessage') and quoted_message.imageMessage and quoted_message.imageMessage.ByteSize() > 0:
                detected_types.append("image")
                image_msg = quoted_message.imageMessage
                mime_type = getattr(image_msg, 'mimetype', 'unknown')
                log.info(f"Found IMAGE message - mime: {mime_type}")
                
            if hasattr(quoted_message, 'documentMessage') and quoted_message.documentMessage and quoted_message.documentMessage.ByteSize() > 0:
                detected_types.append("document")
                doc_msg = quoted_message.documentMessage
                mime_type = getattr(doc_msg, 'mimetype', 'unknown')
                log.info(f"Found DOCUMENT message - mime: {mime_type}")
                
            if hasattr(quoted_message, 'stickerMessage') and quoted_message.stickerMessage and quoted_message.stickerMessage.ByteSize() > 0:
                detected_types.append("sticker")
                log.info("Found STICKER message")
            
            # Log what we detected
            log.info(f"Detected message types: {detected_types}")
            
            # Choose the first valid type (or handle multiple types)
            if len(detected_types) == 1:
                quoted_type = detected_types[0]
                log.info(f"Single type detected: {quoted_type}")
            elif len(detected_types) > 1:
                log.warning(f"Multiple types detected: {detected_types}, using first: {detected_types[0]}")
                quoted_type = detected_types[0]
            else:
                log.warning("No valid message types detected")
                # Enhanced debugging for unknown types
                log.info("Debugging unknown message type:")
                for attr in dir(quoted_message):
                    if not attr.startswith('_') and not attr in ['SerializeToString', 'ParseFromString']:
                        try:
                            val = getattr(quoted_message, attr)
                            if val and hasattr(val, 'ByteSize') and val.ByteSize() > 0:
                                log.info(f"  {attr}: {type(val)} (size: {val.ByteSize()})")
                            elif val and not callable(val):
                                log.info(f"  {attr}: {type(val)} = {str(val)[:100]}")
                        except Exception as e:
                            log.info(f"  {attr}: Error - {e}")
    
    except Exception as e:
        log.error(f"Error in get_quoted_message_info: {e}")
        log.error(traceback.format_exc())
    
    log.info(f"Final detection result - has_quoted: {has_quoted}, quoted_type: {quoted_type}")
    return has_quoted, quoted_message, quoted_type

async def download_media_from_message(client, quoted_message, quoted_type):
    """Download media from quoted message with enhanced fallback methods"""
    try:
        log.info(f"Downloading {quoted_type} from quoted message")
        
        # Method 1: Try thundra_io first (if available and working)
        if THUNDRA_AVAILABLE:
            try:
                log.info(f"Trying thundra_io for {quoted_type}")
                msg_type = get_message_type(quoted_message)
                if isinstance(msg_type, MediaMessageType):
                    file_obj = File.from_message(msg_type)
                    if hasattr(file_obj, 'get_content') and callable(file_obj.get_content):
                        media_bytes = file_obj.get_content()
                        if media_bytes and len(media_bytes) > 0:
                            # Get actual mime type from file_obj if available
                            if hasattr(file_obj, 'mime_type') and file_obj.mime_type:
                                mime_type = file_obj.mime_type
                                log.info(f"Got mime_type from thundra_io: {mime_type}")
                            else:
                                # Fallback mime types
                                mime_type_map = {
                                    "video": "video/mp4",
                                    "audio": "audio/mpeg",
                                    "image": "image/jpeg",
                                    "document": "application/pdf"
                                }
                                mime_type = mime_type_map.get(quoted_type, "application/octet-stream")
                                log.info(f"Using fallback mime_type: {mime_type}")
                            
                            log.info(f"Successfully downloaded {quoted_type} via thundra_io: {len(media_bytes)} bytes")
                            return media_bytes, mime_type
                else:
                    log.warning(f"thundra_io did not detect a media message type for {quoted_type}")
            except Exception as e:
                log.error(f"Error with thundra_io for {quoted_type}: {e}")
        
        # Method 2: Standard download with enhanced error handling
        log.info(f"Trying standard download for {quoted_type}")
        message = Message()
        mime_type = None
        media_obj = None
        
        # Get media object and construct message based on type
        if quoted_type == "audio":
            if hasattr(quoted_message, 'audioMessage') and quoted_message.audioMessage:
                media_obj = quoted_message.audioMessage
                message.audioMessage.CopyFrom(media_obj)
                mime_type = getattr(media_obj, 'mimetype', "audio/ogg")
                log.info(f"Audio message setup complete, mime_type: {mime_type}")
            else:
                log.error("No audioMessage found in quoted message")
                return None, None
                
        elif quoted_type == "video":
            if hasattr(quoted_message, 'videoMessage') and quoted_message.videoMessage:
                media_obj = quoted_message.videoMessage
                message.videoMessage.CopyFrom(media_obj)
                mime_type = getattr(media_obj, 'mimetype', "video/mp4")
                log.info(f"Video message setup complete, mime_type: {mime_type}")
            else:
                log.error("No videoMessage found in quoted message")
                return None, None
                
        elif quoted_type == "image":
            if hasattr(quoted_message, 'imageMessage') and quoted_message.imageMessage:
                media_obj = quoted_message.imageMessage
                message.imageMessage.CopyFrom(media_obj)
                mime_type = getattr(media_obj, 'mimetype', "image/jpeg")
                log.info(f"Image message setup complete, mime_type: {mime_type}")
            else:
                log.error("No imageMessage found in quoted message")
                return None, None
                
        elif quoted_type == "document":
            if hasattr(quoted_message, 'documentMessage') and quoted_message.documentMessage:
                media_obj = quoted_message.documentMessage
                message.documentMessage.CopyFrom(media_obj)
                mime_type = getattr(media_obj, 'mimetype', "application/pdf")
                log.info(f"Document message setup complete, mime_type: {mime_type}")
            else:
                log.error("No documentMessage found in quoted message")
                return None, None
        else:
            log.error(f"Unsupported quoted_type: {quoted_type}")
            return None, None
        
        # Log media properties for debugging
        log.info(f"{quoted_type.title()} message properties:")
        log.info(f"  mimetype: {getattr(media_obj, 'mimetype', 'None')}")
        log.info(f"  fileLength: {getattr(media_obj, 'fileLength', 'None')}")
        if quoted_type in ["audio", "video"]:
            log.info(f"  seconds: {getattr(media_obj, 'seconds', 'None')}")
        if quoted_type == "audio":
            log.info(f"  ptt: {getattr(media_obj, 'ptt', 'None')}")
        log.info(f"  url: {getattr(media_obj, 'url', 'None')}")
        log.info(f"  directPath: {getattr(media_obj, 'directPath', 'None')}")
        
        # Check media availability
        has_url = getattr(media_obj, 'url', None) is not None and getattr(media_obj, 'url', '') != ''
        has_direct_path = getattr(media_obj, 'directPath', None) is not None and getattr(media_obj, 'directPath', '') != ''
        
        log.info(f"Media availability - URL: {has_url}, DirectPath: {has_direct_path}")
        
        # Attempt download with proper error handling
        try:
            log.info(f"Attempting to download {quoted_type} using client.download_any")
            media_bytes = await client.download_any(message)
            
            if media_bytes and len(media_bytes) > 0:
                log.info(f"Successfully downloaded {quoted_type} via standard method: {len(media_bytes)} bytes")
                return media_bytes, mime_type
            else:
                log.error(f"download_any returned empty data for {quoted_type}")
                
        except Exception as download_error:
            log.error(f"download_any failed for {quoted_type}: {download_error}")
            
            # Handle specific error cases
            error_str = str(download_error).lower()
            if "no url present" in error_str:
                log.info(f"Media {quoted_type} has no URL - trying fallback methods...")
                
                # Fallback method 1: For images, try thumbnail
                if quoted_type == "image" and hasattr(media_obj, 'JPEGThumbnail') and media_obj.JPEGThumbnail:
                    log.info("Using JPEG thumbnail as fallback for image")
                    thumbnail_bytes = media_obj.JPEGThumbnail
                    log.info(f"Successfully extracted thumbnail: {len(thumbnail_bytes)} bytes")
                    return thumbnail_bytes, "image/jpeg"
                
                # Fallback method 2: Check for media data in other fields
                # Some messages might have data in different fields
                for field_name in ['mediaData', 'data', 'fileEncSha256', 'fileSha256']:
                    if hasattr(media_obj, field_name):
                        field_data = getattr(media_obj, field_name)
                        if field_data and len(field_data) > 1000:  # Reasonable size for media
                            log.info(f"Found potential media data in {field_name}: {len(field_data)} bytes")
                            # This might be encrypted/encoded data, but let's try
                            return field_data, mime_type
                
                # For now, return error for media without accessible URLs
                log.error(f"Cannot download {quoted_type} - no accessible media URL or data found")
                return None, None
                
            elif "media key" in error_str or "decrypt" in error_str:
                log.error(f"Media decryption failed for {quoted_type} - this might be an old message or encryption issue")
                return None, None
                
            else:
                # Other errors - re-raise
                log.error(f"Unknown download error for {quoted_type}: {download_error}")
                return None, None
        
        # If we reach here, standard download failed but no exception was thrown
        log.error(f"Standard download failed silently for {quoted_type}")
        return None, None
        
    except Exception as e:
        log.error(f"Error downloading {quoted_type} from quoted message: {e}")
        log.error(traceback.format_exc())
        return None, None

# Initialize components
ai_processor = AIProcessor(GEMINI_API_KEY)
downloader = MediaDownloader(ai_processor)

def validate_url(url: str) -> bool:
    """Simple URL validation"""
    return url.startswith(('http://', 'https://')) and '.' in url

def format_size(bytes_size: int) -> str:
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def format_duration(seconds: int) -> str:
    """Format duration"""
    if not seconds:
        return "Unknown"
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def format_number(num: int) -> str:
    """Format large numbers"""
    if not num:
        return "0"
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

@client_factory.event(ConnectedEv)
async def on_connected(_: NewAClient, __: ConnectedEv):
    log.info("⚡ WhatsApp connected with AI features!")

@client_factory.event(MessageEv)
async def on_message(client: NewAClient, message: MessageEv):
    await handle_message(client, message)

async def handle_message(client, message):
    try:
        chat = message.Info.MessageSource.Chat
        
        # Extract message text
        text = ""
        if hasattr(message.Message, 'conversation') and message.Message.conversation:
            text = message.Message.conversation
        elif hasattr(message.Message, 'extendedTextMessage') and message.Message.extendedTextMessage.text:
            text = message.Message.extendedTextMessage.text
        
        text = text.strip()
        
        # Get quoted message info
        has_quoted, quoted_message, quoted_type = await get_quoted_message_info(message)
        
        # Basic commands
        if text.lower() == "ping":
            await client.reply_message("🏓 Pong! AI features ready!", message)
            return
            
        elif text.lower() in ["help", "/help", "menu"]:
            help_text = """
🤖 *Universal Media Downloader + AI*

*📥 Download Commands:*
• `mp3 <URL>` - Download audio (MP3)
• `video <URL> [quality]` - Download video
• `info <URL>` - Get media information

*🧠 AI-Powered Commands:*
• `transcribe <URL>` - Audio transcription
• `summary <URL>` - AI content summary  
• `analyze <URL>` - Full AI analysis
• `smart <URL>` - Download + transcribe + summary

*🎬 YouTube Content Commands:*
• `ytvideo <URL>` - Analyze video for YouTube
• `ytaudio <URL>` - Analyze audio for YouTube

*🎯 Media Analysis (Reply to media):*
• `analyze` - Analyze quoted media with AI
• `transcribe` - Transcribe quoted audio/video

*🌐 Supported Platforms:*
✅ YouTube, TikTok, Instagram, Facebook
✅ Twitter, SoundCloud, Vimeo, Twitch
✅ And 1000+ other platforms!

*💡 AI Examples:*
> `transcribe https://youtu.be/xxxxx`
> `summary https://vt.tiktok.com/xxxxx`
> `smart https://youtu.be/xxxxx`
> `ytvideo https://youtu.be/xxxxx`
> Reply to audio → `transcribe`

*Powered by Gemini AI* ✨
"""
            await client.send_message(chat, help_text)
            return
        
        # Parse command
        parts = text.split()
        if len(parts) < 1:
            return
            
        command = parts[0].lower()
        
        # Handle quoted media AI commands
        if has_quoted and command in ["analyze", "transcribe"]:
            log.info(f"Processing quoted {quoted_type} with command: {command}")
            
            # Check if media type is supported for the command
            if command == "transcribe":
                if quoted_type not in ["audio", "video"]:
                    await client.send_message(chat, f"❌ Transcription only supports audio and video. Detected: {quoted_type}")
                    return
                await client.send_message(chat, f"🎵📝 Transcribing {quoted_type}...")
            elif command == "analyze":
                if quoted_type not in ["audio", "video", "image"]:
                    await client.send_message(chat, f"❌ Analysis supports audio, video, and image. Detected: {quoted_type}")
                    return
                await client.send_message(chat, f"🧠🔍 Analyzing {quoted_type}...")
            
            # Download media
            media_bytes, mime_type = await download_media_from_message(client, quoted_message, quoted_type)
            
            if media_bytes:
                log.info(f"Successfully downloaded {quoted_type}, size: {len(media_bytes)} bytes, mime: {mime_type}")
                
                if command == "transcribe":
                    # For video files, we still use transcribe_audio since Gemini can extract audio
                    if quoted_type == "video":
                        await client.send_message(chat, "📹➡️🎵 Extracting audio from video for transcription...")
                    
                    result = await ai_processor.transcribe_audio(media_bytes, mime_type)
                    if result["success"]:
                        # Format response based on media type
                        if quoted_type == "audio":
                            response = f"🎵📝 *Audio Transcription:*\n\n{result['transcription']}"
                        else:  # video
                            response = f"📹📝 *Video Transcription:*\n\n{result['transcription']}"
                        await client.send_message(chat, response)
                    else:
                        await client.send_message(chat, f"❌ Transcription failed: {result['error']}")
                
                elif command == "analyze":
                    # Media analysis with appropriate prompts
                    if quoted_type == "audio":
                        prompt = "Analyze this audio content. Describe what you hear, identify the type of content (music, speech, etc.), and provide insights. Respond in Indonesian."
                    elif quoted_type == "video":
                        prompt = "Analyze this video content. Describe what you see and hear, identify the type of content, and provide insights. Respond in Indonesian."
                    elif quoted_type == "image":
                        prompt = "Analyze this image in detail. Describe what you see, identify objects, people, text, and provide insights. Respond in Indonesian."
                    else:
                        prompt = "Analyze this media content and provide insights. Respond in Indonesian."
                    
                    result = await ai_processor.analyze_media(media_bytes, mime_type, prompt)
                    if result["success"]:
                        # Format response based on media type
                        media_emoji = {"audio": "🎵", "video": "📹", "image": "🖼️"}.get(quoted_type, "📄")
                        response = f"{media_emoji}🔍 *{quoted_type.title()} Analysis:*\n\n{result['analysis']}"
                        await client.send_message(chat, response)
                    else:
                        await client.send_message(chat, f"❌ Analysis failed: {result['error']}")
            else:
                # More specific error messages based on media type
                if quoted_type == "audio":
                    error_msg = "❌ Cannot download audio. This might be:\n"
                    error_msg += "• Voice note without accessible URL\n"
                    error_msg += "• Forwarded audio from old message\n" 
                    error_msg += "• Audio with encryption issues\n\n"
                    error_msg += "💡 Try with: Recent audio files or voice notes you recorded"
                elif quoted_type == "video":
                    error_msg = "❌ Cannot download video. This might be:\n"
                    error_msg += "• Large video without accessible URL\n"
                    error_msg += "• Forwarded video from old message\n"
                    error_msg += "• Video with decryption issues\n\n"
                    error_msg += "💡 Try with: Recent videos or smaller file sizes"
                elif quoted_type == "image":
                    error_msg = "❌ Cannot download image. This might be:\n"
                    error_msg += "• Forwarded image from old message\n"
                    error_msg += "• Image with accessibility issues\n\n"
                    error_msg += "💡 Try with: Recent photos you took or received"
                else:
                    error_msg = f"❌ Cannot download {quoted_type}. Please try with a recent media file."
                
                await client.send_message(chat, error_msg)
            return
        
        # URL-based commands
        if len(parts) < 2:
            return
            
        url = parts[1]
        quality = parts[2] if len(parts) > 2 else "720p"
        
        # Validate URL
        if not validate_url(url):
            await client.send_message(chat, "❌ Invalid URL! Use: https://...")
            return
        
        platform = downloader.get_platform_name(url)
        
        # NEW YOUTUBE ANALYSIS COMMANDS
        if command == "ytvideo":
            await client.send_message(chat, f"🎬📊 Analyzing video for YouTube content from {platform}...")
            
            result = await downloader.download_for_youtube_analysis(url, "video", str(chat))
            
            if result["success"] and result.get("youtube_analysis", {}).get("success"):
                info = result["info"]
                youtube_analysis = result["youtube_analysis"]["youtube_analysis"]
                
                response = f"🎬 *Original: {info['title']}*\n"
                response += f"👤 {info['uploader']} | {platform}\n"
                response += f"⏱️ Duration: {format_duration(info['duration'])}\n\n"
                response += f"📊 *ANALISIS YOUTUBE CONTENT:*\n\n"
                response += youtube_analysis
                
                await client.send_message(chat, response)
            else:
                error_msg = result.get("youtube_analysis", {}).get("error") if result.get("success") else result.get("error", "Unknown error")
                await client.send_message(chat, f"❌ YouTube video analysis failed: {error_msg}")
            return
            
        elif command == "ytaudio":
            await client.send_message(chat, f"🎵📊 Analyzing audio for YouTube content from {platform}...")
            
            result = await downloader.download_for_youtube_analysis(url, "audio", str(chat))
            
            if result["success"] and result.get("youtube_analysis", {}).get("success"):
                info = result["info"]
                youtube_analysis = result["youtube_analysis"]["youtube_analysis"]
                
                response = f"🎵 *Original: {info['title']}*\n"
                response += f"👤 {info['uploader']} | {platform}\n"
                response += f"⏱️ Duration: {format_duration(info['duration'])}\n\n"
                response += f"📊 *ANALISIS YOUTUBE CONTENT:*\n\n"
                response += youtube_analysis
                
                await client.send_message(chat, response)
            else:
                error_msg = result.get("youtube_analysis", {}).get("error") if result.get("success") else result.get("error", "Unknown error")
                await client.send_message(chat, f"❌ YouTube audio analysis failed: {error_msg}")
            return
        
        # AI-powered download commands
        if command == "transcribe":
            await client.send_message(chat, f"🎵📝 Downloading and transcribing from {platform}...")
            
            result = await downloader.download_with_ai(url, ["transcribe"], quality, str(chat))
            
            if result["success"] and "transcription" in result["ai_results"]:
                transcription = result["ai_results"]["transcription"]
                if transcription["success"]:
                    info = result["info"]
                    response = f"🎵 *{info['title']}*\n"
                    response += f"👤 {info['uploader']} | {platform}\n\n"
                    response += f"📝 *Transcription:*\n{transcription['transcription']}"
                    await client.send_message(chat, response)
                else:
                    await client.send_message(chat, f"❌ Transcription failed: {transcription['error']}")
            else:
                await client.send_message(chat, f"❌ Download failed: {result.get('error', 'Unknown error')}")
            return
        
        elif command == "summary":
            await client.send_message(chat, f"🎵📊 Downloading and summarizing from {platform}...")
            
            result = await downloader.download_with_ai(url, ["transcribe", "summary"], quality, str(chat))
            
            if result["success"] and "summary" in result["ai_results"]:
                summary = result["ai_results"]["summary"]
                if summary["success"]:
                    info = result["info"]
                    response = f"🎵 *{info['title']}*\n"
                    response += f"👤 {info['uploader']} | {platform}\n\n"
                    response += f"📊 *AI Summary:*\n{summary['summary']}"
                    await client.send_message(chat, response)
                else:
                    await client.send_message(chat, f"❌ Summary failed: {summary['error']}")
            else:
                await client.send_message(chat, f"❌ Download failed: {result.get('error', 'Unknown error')}")
            return
        
        elif command == "smart":
            await client.send_message(chat, f"🧠✨ Full AI processing from {platform}...")
            
            result = await downloader.download_with_ai(url, ["transcribe", "summary", "analyze"], quality, str(chat))
            
            if result["success"]:
                info = result["info"]
                ai_results = result["ai_results"]
                
                response = f"🎵 *{info['title']}*\n"
                response += f"👤 {info['uploader']} | {platform}\n"
                response += f"⏱️ Duration: {format_duration(info['duration'])}\n"
                response += f"👁️ Views: {format_number(info['view_count'])}\n\n"
                
                # Add transcription if available
                if "transcription" in ai_results and ai_results["transcription"].get("success"):
                    transcription = ai_results["transcription"]["transcription"]
                    # Limit transcription length for display
                    if len(transcription) > 500:
                        transcription = transcription[:500] + "...\n\n[Transcription truncated]"
                    response += f"📝 *Transcription:*\n{transcription}\n\n"
                
                # Add summary if available
                if "summary" in ai_results and ai_results["summary"].get("success"):
                    response += f"📊 *AI Summary:*\n{ai_results['summary']['summary']}\n\n"
                
                # Add analysis if available
                if "analysis" in ai_results and ai_results["analysis"].get("success"):
                    response += f"🔍 *Video Analysis:*\n{ai_results['analysis']['analysis']}"
                
                await client.send_message(chat, response)
                
                # Send video file if available
                if "video_file" in result and result["video_file"].get("success"):
                    video_file = result["video_file"]
                    file_size = video_file["file_size"]
                    
                    # Check WhatsApp video limit
                    if file_size <= 64 * 1024 * 1024:
                        await client.send_message(chat, f"📹 Sending video ({format_size(file_size)})...")
                        try:
                            await client.send_video(chat, video_file["file_path"])
                            # Cleanup after sending
                            await asyncio.sleep(2)
                            if os.path.exists(video_file["file_path"]):
                                os.remove(video_file["file_path"])
                        except Exception as e:
                            await client.send_message(chat, f"❌ Failed to send video: {str(e)}")
                            if os.path.exists(video_file["file_path"]):
                                os.remove(video_file["file_path"])
                    else:
                        await client.send_message(chat, f"⚠️ Video too large ({format_size(file_size)}) for WhatsApp")
                        if os.path.exists(video_file["file_path"]):
                            os.remove(video_file["file_path"])
                        
            else:
                await client.send_message(chat, f"❌ Smart processing failed: {result.get('error', 'Unknown error')}")
            return
        
        elif command == "analyze":
            if len(parts) < 2:
                return
                
            await client.send_message(chat, f"🔍 Analyzing content from {platform}...")
            
            result = await downloader.download_with_ai(url, ["analyze"], quality, str(chat))
            
            if result["success"] and "analysis" in result["ai_results"]:
                analysis = result["ai_results"]["analysis"]
                if analysis.get("success"):
                    info = result["info"]
                    response = f"🎬 *{info['title']}*\n"
                    response += f"👤 {info['uploader']} | {platform}\n\n"
                    response += f"🔍 *AI Analysis:*\n{analysis['analysis']}"
                    await client.send_message(chat, response)
                else:
                    await client.send_message(chat, f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
            else:
                await client.send_message(chat, f"❌ Download failed: {result.get('error', 'Unknown error')}")
            return
        
        # Info command
        elif command in ["info", "i"]:
            await client.send_message(chat, f"🔍 Getting info from {platform}...")
            
            info = await downloader.get_info(url)
            
            if info["success"]:
                info_text = f"""
📺 *{info['title']}*

👤 *Creator:* {info['uploader']}
🌐 *Platform:* {info['platform']}
⏱️ *Duration:* {format_duration(info['duration'])}
👁️ *Views:* {format_number(info['view_count'])}

📝 *Description:*
{info['description']}...
"""
                await client.send_message(chat, info_text)
            else:
                await client.send_message(chat, f"❌ Error: {info['error']}")
            return
        
        # Audio download
        elif command in ["mp3", "audio", "music", "a"]:
            await client.send_message(chat, f"🎵 Downloading audio from {platform}...")
            
            # Get info first
            info = await downloader.get_info(url)
            if info["success"]:
                await client.send_message(chat, f"📝 {info['title']}")
            
            result = await downloader.download(url, "audio", "best", str(chat))
            
            if result["success"]:
                file_path = result["file_path"]
                file_size = result["file_size"]
                
                # Check WhatsApp audio limit (~16MB)
                if file_size > 16 * 1024 * 1024:
                    await client.send_message(chat, f"❌ File too large ({format_size(file_size)}). WhatsApp limit: ~16MB")
                    os.remove(file_path)
                    return
                
                await client.send_message(chat, f"✅ Sending audio ({format_size(file_size)})...")
                
                try:
                    await client.send_audio(chat, file_path)
                    await client.send_message(chat, f"🎵 Audio sent! Size: {format_size(file_size)}")
                    
                    # Cleanup
                    await asyncio.sleep(2)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        
                except Exception as e:
                    await client.send_message(chat, f"❌ Send failed: {str(e)}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                await client.send_message(chat, f"❌ Download failed: {result['error']}")
            return
        
        # Video download
        elif command in ["video", "vid", "v", "mp4"]:
            await client.send_message(chat, f"🎬 Downloading video from {platform} ({quality})...")
            
            # Get info first
            info = await downloader.get_info(url)
            if info["success"]:
                await client.send_message(chat, f"📝 {info['title']}")
            
            result = await downloader.download(url, "video", quality, str(chat))
            
            if result["success"]:
                file_path = result["file_path"]
                file_size = result["file_size"]
                
                # Check WhatsApp video limit (~64MB)
                if file_size > 64 * 1024 * 1024:
                    await client.send_message(chat, f"❌ File too large ({format_size(file_size)}). WhatsApp limit: ~64MB")
                    os.remove(file_path)
                    return
                
                await client.send_message(chat, f"✅ Sending video ({format_size(file_size)})...")
                
                try:
                    await client.send_video(chat, file_path)
                    await client.send_message(chat, f"🎬 Video sent! Size: {format_size(file_size)}")
                    
                    # Cleanup
                    await asyncio.sleep(2)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        
                except Exception as e:
                    await client.send_message(chat, f"❌ Send failed: {str(e)}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                await client.send_message(chat, f"❌ Download failed: {result['error']}")
            return
        
        # Direct AI chat with Gemini
        elif command == "ai" and len(parts) > 1:
            query = " ".join(parts[1:])
            await client.send_message(chat, "🧠 Processing with Gemini AI...")
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"Respond in Indonesian. {query}"
                            }
                        ]
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(ai_processor.gemini_url, json=payload, headers=headers) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            response_json = json.loads(response_text)
                            try:
                                ai_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
                                await client.send_message(chat, f"🤖 *Gemini AI:*\n\n{ai_response}")
                            except (KeyError, IndexError):
                                await client.send_message(chat, "❌ Failed to parse AI response")
                        else:
                            await client.send_message(chat, f"❌ AI error: {response.status}")
            except Exception as e:
                await client.send_message(chat, f"❌ AI error: {str(e)}")
            return
            
    except Exception as e:
        log.error(f"Error in message handler: {e}")
        log.error(traceback.format_exc())
        try:
            await client.send_message(chat, f"❌ Error: {str(e)}")
        except:
            pass

# Background cleanup task
async def cleanup_task():
    """Auto cleanup old files"""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            downloader.cleanup_old_files(24)  # Remove files older than 24h
        except Exception as e:
            log.error(f"Cleanup task error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Universal Media Downloader Bot with AI...")
    print("🧠 AI Features: Transcription, Summarization, Analysis")
    print("🎬 NEW: YouTube Content Analysis (ytvideo, ytaudio)")
    print("🌐 Supports 1000+ platforms including:")
    print("   📺 YouTube, TikTok, Instagram, Facebook")
    print("   🎵 SoundCloud, Spotify, Twitter")
    print("   🎮 Twitch, Reddit, Vimeo, and more!")
    print("⚡ Commands: mp3, video, transcribe, summary, smart, analyze, ai, ytvideo, ytaudio")
    print("⚠️  Make sure yt-dlp is installed and Gemini API key is valid!")
    
    # Start cleanup task
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_task())
    
    # Run bot
    loop.run_until_complete(client_factory.run())

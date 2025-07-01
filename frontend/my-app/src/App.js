import React, { useState, useRef } from 'react';
import './App.css';

const LAUGHING_PEOPLE_PNG = 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80'; // Example stock photo

const PROJECT_DESCRIPTION = `Upload your voice message and discover which celebrity you sound like! Our AI matches your voice to famous personalities and lets you share the fun. See who tops the leaderboard for the most similar voices!`;

const MOCK_LEADERBOARD = [
  { name: 'Shelby', count: 100 },
  { name: 'Morgan Freeman', count: 87 },
  { name: 'Ariana Grande', count: 75 },
  { name: 'Tom Hanks', count: 60 },
  { name: 'Taylor Swift', count: 55 },
];

const YOUTUBE_VIDEOS = [
  'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  'https://www.youtube.com/watch?v=3JZ_D3ELwOQ',
  'https://www.youtube.com/watch?v=9bZkp7q19f0',
  'https://www.youtube.com/watch?v=L_jWHffIx5E',
  'https://www.youtube.com/watch?v=Zi_XLOBDo_Y',
];

function App() {
  const [audioFile, setAudioFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState('upload');
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordError, setRecordError] = useState('');
  const audioRef = useRef(null);
  const chunksRef = useRef([]);
  const [mediaStream, setMediaStream] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState(YOUTUBE_VIDEOS[0]);

  const handleFileChange = (e) => {
    setAudioFile(e.target.files[0]);
    setResult(null);
    setRecordedAudio(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!audioFile && !recordedAudio) return;
    setLoading(true);
    const fileToUse = audioFile || recordedAudio;
    // Pick a random YouTube video for the result
    const randomUrl = YOUTUBE_VIDEOS[Math.floor(Math.random() * YOUTUBE_VIDEOS.length)];
    setTimeout(() => {
      setResult({
        image: 'https://randomuser.me/api/portraits/men/32.jpg',
        audio: URL.createObjectURL(fileToUse),
      });
      setYoutubeUrl(randomUrl);
      setLoading(false);
    }, 2000);
  };

  const handlePlayPause = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  const handleAudioPlay = () => {
    setIsPlaying(true);
  };

  const handleAudioPause = () => {
    setIsPlaying(false);
  };

  const handleRecord = async () => {
    if (isRecording) {
      if (mediaRecorder) {
        mediaRecorder.stop();
      }
      setIsRecording(false);
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        setMediaStream(null);
      }
      return;
    }
    setRecordError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMediaStream(stream);
      // Check for supported MIME types
      let mimeType = '';
      if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
        mimeType = 'audio/ogg';
      } else if (MediaRecorder.isTypeSupported('audio/wav')) {
        mimeType = 'audio/wav';
      } else {
        setRecordError('No supported audio format found for recording.');
        return;
      }
      const recorder = new window.MediaRecorder(stream, { mimeType });
      setMediaRecorder(recorder);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const file = new File([blob], 'recorded-message.' + mimeType.split('/')[1], { type: mimeType });
        setRecordedAudio(file);
        setAudioFile(null);
        if (mediaStream) {
          mediaStream.getTracks().forEach(track => track.stop());
          setMediaStream(null);
        }
      };
      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setRecordError('Microphone access denied or not available.');
    }
  };

  // Playback error handling
  const [playbackError, setPlaybackError] = useState('');
  const handleAudioError = () => {
    setPlaybackError('Playback failed. Your browser may not support this audio format.');
  };

  return (
    <div className="main-container">
      <nav className="navbar">
        <div className="nav-logo">Your Celeb Voice</div>
        <div className="nav-links">
          <button className={page === 'upload' ? 'active' : ''} onClick={() => setPage('upload')}>Upload</button>
          <button className={page === 'leaderboard' ? 'active' : ''} onClick={() => setPage('leaderboard')}>Leaderboard</button>
        </div>
      </nav>
      {page === 'upload' && (
        <header className="header-section">
          <img src={LAUGHING_PEOPLE_PNG} alt="People laughing" className="header-bg" />
          <div className="header-overlay">
            <h2>Find Your Celebrity Voice Match!</h2>
            <p>{PROJECT_DESCRIPTION}</p>
          </div>
        </header>
      )}
      {page === 'upload' && (
        <form onSubmit={handleSubmit} className="upload-form">
          <input
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
            disabled={loading || isRecording}
          />
          <button
            type="button"
            className={isRecording ? 'record-btn recording' : 'record-btn'}
            onClick={handleRecord}
            disabled={loading}
          >
            {isRecording ? 'Stop Recording' : 'Record Voice Message'}
          </button>
          {recordError && <div className="record-error">{recordError}</div>}
          {recordedAudio && (
            <audio controls src={URL.createObjectURL(recordedAudio)} className="audio-player" style={{ marginTop: 10 }} onError={handleAudioError} />
          )}
          {playbackError && <div className="record-error">{playbackError}</div>}
          <button type="submit" disabled={(!audioFile && !recordedAudio) || loading}>
            {loading ? 'Processing...' : 'Upload Voice Message'}
          </button>
        </form>
      )}
      {page === 'upload' && result && (
        <div className="result-section">
          <div className="celeb-name-large">Shelby</div>
          <a
            href={youtubeUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Watch the YouTube video from which this voice was taken"
            className="celeb-avatar-link"
            style={{ textDecoration: 'none' }}
          >
            <img src={result.image} alt="Celebrity" className="celeb-image" />
          </a>
          <div className="audio-scroll-wrapper">
            <audio
              ref={audioRef}
              src={result.audio}
              className="audio-player"
              onEnded={handleAudioEnded}
              onPlay={handleAudioPlay}
              onPause={handleAudioPause}
              style={{ display: 'none' }}
            />
            <button className="play-btn" onClick={handlePlayPause}>
              {isPlaying ? 'Pause' : 'Play'}
            </button>
          </div>
        </div>
      )}
      {page === 'leaderboard' && (
        <div className="leaderboard-section">
          <h3>Leaderboard: Most Matched Celebrities</h3>
          <ul>
            {MOCK_LEADERBOARD.map((item, idx) => (
              <li key={item.name}>
                <span className="celeb-name">{idx + 1}. {item.name}</span>
                <span className="celeb-count">{item.count} times</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;

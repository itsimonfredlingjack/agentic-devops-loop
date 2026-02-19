use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};
use tauri::State;

pub struct MicState {
    recording: Arc<Mutex<bool>>,
    buffer: Arc<Mutex<Vec<i16>>>,
    stream: Arc<Mutex<Option<cpal::Stream>>>,
}

impl Default for MicState {
    fn default() -> Self {
        Self {
            recording: Arc::new(Mutex::new(false)),
            buffer: Arc::new(Mutex::new(Vec::new())),
            stream: Arc::new(Mutex::new(None)),
        }
    }
}

// SAFETY: cpal::Stream is Send on all platforms we target.
// The stream is behind Arc<Mutex<>> and only accessed from one thread at a time.
unsafe impl Send for MicState {}
unsafe impl Sync for MicState {}

const SAMPLE_RATE: u32 = 16_000;

#[tauri::command]
pub fn start_mic(state: State<'_, MicState>) -> Result<String, String> {
    let mut recording = state.recording.lock().map_err(|e| e.to_string())?;
    if *recording {
        return Err("Already recording".into());
    }

    // Clear previous buffer
    {
        let mut buf = state.buffer.lock().map_err(|e| e.to_string())?;
        buf.clear();
    }

    let host = cpal::default_host();
    let device = host
        .default_input_device()
        .ok_or("No input device available")?;

    let config = cpal::StreamConfig {
        channels: 1,
        sample_rate: cpal::SampleRate(SAMPLE_RATE),
        buffer_size: cpal::BufferSize::Default,
    };

    let buffer = Arc::clone(&state.buffer);
    let recording_flag = Arc::clone(&state.recording);

    let stream = device
        .build_input_stream(
            &config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                let is_recording = recording_flag.lock().map(|r| *r).unwrap_or(false);
                if !is_recording {
                    return;
                }
                // Convert f32 samples to i16
                let samples: Vec<i16> = data
                    .iter()
                    .map(|&s| {
                        let clamped = s.clamp(-1.0, 1.0);
                        (clamped * i16::MAX as f32) as i16
                    })
                    .collect();
                if let Ok(mut buf) = buffer.lock() {
                    buf.extend_from_slice(&samples);
                }
            },
            move |err| {
                eprintln!("Audio stream error: {}", err);
            },
            None,
        )
        .map_err(|e| format!("Failed to build input stream: {}", e))?;

    stream.play().map_err(|e| format!("Failed to start stream: {}", e))?;

    *recording = true;
    let mut stream_holder = state.stream.lock().map_err(|e| e.to_string())?;
    *stream_holder = Some(stream);

    Ok("Recording started".into())
}

#[tauri::command]
pub fn stop_mic(state: State<'_, MicState>) -> Result<Vec<i16>, String> {
    let mut recording = state.recording.lock().map_err(|e| e.to_string())?;
    if !*recording {
        return Err("Not recording".into());
    }

    *recording = false;

    // Drop the stream to stop recording
    {
        let mut stream_holder = state.stream.lock().map_err(|e| e.to_string())?;
        *stream_holder = None;
    }

    let buf = state.buffer.lock().map_err(|e| e.to_string())?;
    Ok(buf.clone())
}

use hound::{SampleFormat, WavSpec, WavWriter};
use reqwest::multipart;
use serde::Deserialize;
use std::io::Cursor;

const SAMPLE_RATE: u32 = 16_000;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SendAudioArgs {
    pub samples: Vec<i16>,
    pub server_url: String,
}

#[derive(serde::Serialize)]
pub struct TranscriptionResult {
    pub text: String,
    pub job_id: String,
}

fn encode_wav(samples: &[i16]) -> Result<Vec<u8>, String> {
    let spec = WavSpec {
        channels: 1,
        sample_rate: SAMPLE_RATE,
        bits_per_sample: 16,
        sample_format: SampleFormat::Int,
    };

    let mut cursor = Cursor::new(Vec::new());
    {
        let mut writer =
            WavWriter::new(&mut cursor, spec).map_err(|e| format!("WAV write error: {}", e))?;
        for &sample in samples {
            writer
                .write_sample(sample)
                .map_err(|e| format!("WAV sample error: {}", e))?;
        }
        writer
            .finalize()
            .map_err(|e| format!("WAV finalize error: {}", e))?;
    }

    Ok(cursor.into_inner())
}

#[tauri::command]
pub async fn send_audio(samples: Vec<i16>, server_url: String) -> Result<TranscriptionResult, String> {
    let wav_bytes = encode_wav(&samples)?;

    let part = multipart::Part::bytes(wav_bytes)
        .file_name("recording.wav")
        .mime_str("audio/wav")
        .map_err(|e| format!("MIME error: {}", e))?;

    let form = multipart::Form::new().part("audio", part);

    let url = format!("{}/api/transcribe", server_url.trim_end_matches('/'));

    let client = reqwest::Client::new();
    let resp = client
        .post(&url)
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("HTTP request failed: {}", e))?;

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("Server error {}: {}", status, body));
    }

    let result: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("JSON parse error: {}", e))?;

    Ok(TranscriptionResult {
        text: result["text"].as_str().unwrap_or("").to_string(),
        job_id: result["job_id"].as_str().unwrap_or("").to_string(),
    })
}

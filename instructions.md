# Python Tuner — Build Steps

## 1. Project Setup
- Create a virtual environment
- Install dependencies: sounddevice, numpy, and optionally librosa
- Verify mic input works by recording a short clip and checking it has data

## 2. Capture Audio Stream
- Open a real-time input stream from the default microphone
- Choose a sample rate (44100 Hz) and block size (4096 samples)
- Collect each block of raw audio samples via a callback function

## 3. Detect Fundamental Frequency
- Take the incoming audio block and compute its FFT
- Identify the frequency bin with the highest magnitude
- Ignore bins below ~50 Hz to filter out DC noise and rumble
- Return the peak frequency in Hz

## 4. Map Frequency to Musical Note
- Define A4 = 440 Hz as the reference pitch
- Compute the number of semitones between the detected frequency and A4 using a log base-2 formula
- Round to the nearest integer semitone to get the closest note
- Use the semitone index modulo 12 to look up the note name
- Compute the octave number from the semitone offset
- Compute cents deviation as the fractional semitone × 100

## 5. Determine Tuning Status
- If cents deviation is within ±5, mark as "in tune"
- If positive, mark as "sharp"
- If negative, mark as "flat"

## 6. Display Output in the Terminal
- Clear the previous line on each update to produce an in-place display
- Show the detected note name and octave
- Show the frequency in Hz
- Show the cents deviation with a +/- sign
- Show a visual indicator (e.g. a bar or arrow) pointing left for flat, right for sharp, center for in tune

## 7. Add Silence Detection
- Compute the RMS (root mean square) amplitude of each audio block
- If RMS is below a threshold, skip pitch detection and show a waiting state
- This prevents garbage output when no instrument is playing

## 8. Tune the Detection (optional improvements)
- Increase block size for better low-frequency resolution
- Apply a Hann window to the audio block before FFT to reduce spectral leakage
- Use parabolic interpolation around the FFT peak to improve frequency precision
- Consider switching to the YIN algorithm via librosa for more accurate pitch on complex tones

## 9. Graceful Exit
- Catch keyboard interrupt to stop the stream cleanly
- Close the audio stream and print a final message on exit

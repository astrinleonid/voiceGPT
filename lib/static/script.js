const form = document.getElementById('ttsForm');
const promptInput = document.getElementById('prompt');
const speakerSelect = document.getElementById('speaker');
const audioPlayer = document.getElementById('audioPlayer');

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const prompt = promptInput.value;
    const speaker = speakerSelect.value;

    if (!prompt) {
        alert('Please enter a prompt');
        return;
    }

    const response = await fetch(`/get_response?prompt=${encodeURIComponent(prompt)}&speaker=${encodeURIComponent(speaker)}`);
    const blob = await response.blob();
    const audioURL = URL.createObjectURL(blob);
    audioPlayer.src = audioURL;
    audioPlayer.play();
});
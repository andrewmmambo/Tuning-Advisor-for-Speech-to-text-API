from flask import Flask, request, jsonify
import speech_recognition as sr
import nltk
import statistics

app = Flask(__name__)

# Example grammar rules
grammar_rules = {
    'capitalization': ['Start sentences with a capital letter.'],
    'punctuation': ['End sentences with a period.', 'Use commas to separate clauses.']
}

@app.route('/speech-to-text', methods=['POST'])
def transcribe_speech():
    # Check if audio file is present in the request
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400

    # Get the audio file from the request
    audio_file = request.files['audio']

    # Check if the file is empty
    if audio_file.filename == '':
        return jsonify({'error': 'No audio file selected'}), 400

    # Initialize the SpeechRecognizer
    recognizer = sr.Recognizer()

    # Read the audio file
    with sr.AudioFile(audio_file) as source:
        try:
            # Attempt to recognize the speech
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return jsonify({'error': 'Speech could not be recognized'}), 400
        except sr.RequestError:
            return jsonify({'error': 'Speech recognition service unavailable'}), 500

    # Perform grammar evaluation
    grammar_errors = {}
    sentences = nltk.sent_tokenize(text)
    for sentence in sentences:
        words = nltk.word_tokenize(sentence)
        tagged_words = nltk.pos_tag(words)
        for word, tag in tagged_words:
            if tag == 'NNP':  # Proper noun, check for capitalization
                if not word[0].isupper():
                    grammar_errors[sentence] = 'Start sentence with a capital letter.'

    # Perform problematic input states detection
    sentence_lengths = [len(sentence.split()) for sentence in sentences]
    outlier_count = sum(1 for length in sentence_lengths if length > statistics.mean(sentence_lengths) * 2)

    # Generate tuning advice
    tuning_advice = []
    if grammar_errors:
        tuning_advice.append('Check for capitalization errors.')
    if outlier_count > 0:
        tuning_advice.append('Some sentences are unusually long. Provide shorter examples.')

    # Return transcribed text and analysis results
    return jsonify({
        'transcribed_text': text,
        'grammar_evaluation': grammar_errors,
        'problematic_input_states': {'outlier_count': outlier_count},
        'tuning_advice': tuning_advice
    })

if __name__ == '__main__':
    app.run(debug=True)

import streamlit as st
import numpy as np
from pydub import AudioSegment
from presets import Preset
import librosa as librosa
import librosa.display
from bing_image_downloader import downloader
from keras.layers import Input, Dense, Activation, BatchNormalization, Flatten, Conv2D, MaxPooling2D
from keras.models import Model
from keras.initializers import glorot_uniform
from keras.preprocessing.image import load_img, img_to_array
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.cm as cm
from matplotlib.colors import Normalize


def cnn(input_shape=(288, 432, 4), classes=9):
    def step(dim, X):
        X = Conv2D(dim, kernel_size=(3, 3), strides=(1, 1))(X)
        X = BatchNormalization(axis=3)(X)
        X = Activation('relu')(X)
        return MaxPooling2D((2, 2))(X)
    X_input = Input(input_shape)
    X = X_input
    layer_dims = [8, 16, 32, 64, 128, 256]
    for dim in layer_dims:
        X = step(dim, X)

    X = Flatten()(X)
    X = Dense(classes, activation='softmax',
              name=f'fc{classes}',  kernel_initializer=glorot_uniform(seed=9))(X)
    model = Model(inputs=X_input, outputs=X, name='cnn')
    return model


def convert_mp3_to_wav(music_file):
    sound = AudioSegment.from_mp3(music_file)
    sound.export("music_file.wav", format="wav")


def extract_relevant(wav_file, t1, t2):
    wav = AudioSegment.from_wav(wav_file)
    wav = wav[1000*t1:1000*t2]
    wav.export("extracted.wav", format='wav')


def create_melspectrogram(wav_file):
    y, sr = librosa.load(wav_file, duration=3)
    mels = librosa.feature.melspectrogram(y=y, sr=sr)
    fig = plt.Figure()
    FigureCanvasAgg(fig)
    plt.imshow(librosa.power_to_db(mels, ref=np.max))
    plt.savefig('melspectrogram.png')


def download_image():
    filename = file.name
    filename = str.split(filename, "(")[0]
    downloader.download(filename + "Spotify", limit=1, output_dir='/',
                        adult_filter_off=True, force_replace=False, timeout=60)
    return filename


def predict(image_data, model):
    image = img_to_array(image_data).reshape((1, 288, 432, 4))
    prediction = model.predict(image / 255)
    prediction = prediction.reshape((9, ))
    class_label = np.argmax(prediction)
    return class_label, prediction


librosa_preset = Preset(librosa)
librosa_preset['sr'] = 44100

st.write("""# Music Genre Classifier""")
st.write("##### A Convolutional Neural Network Classifier by Eric Zacharia")
file = st.file_uploader(
    "Upload your MP3 File, and watch the CNN model classify the music genre.", type=["mp3"])
class_labels = ['blues', 'classical', 'country',
                'disco', 'hiphop', 'metal', 'pop', 'reggae', 'rock']

model = cnn(input_shape=(288, 432, 4), classes=9)
model.load_weights("CNNModelWeights.h5")

if file is not None:
    convert_mp3_to_wav(file)
    extract_relevant("music_file.wav", 40, 50)
    create_melspectrogram("extracted.wav")
    image_data = load_img('melspectrogram.png',
                          color_mode='rgba', target_size=(288, 432))

    filename = download_image()
    st.write(filename)
    st.audio(file, "audio/mp3")

    class_label, prediction = predict(image_data, model)
    prediction = prediction.reshape((9,))
    color_data = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    my_cmap = cm.get_cmap('jet')
    my_norm = Normalize(vmin=0, vmax=9)

    st.write(f"### Genre Prediction: {class_labels[class_label]}")
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(x=class_labels, height=prediction,
           color=my_cmap(my_norm(color_data)))
    plt.xticks(rotation=45)
    ax.set_title(
        "Probability Distribution Of The Given Song Over Different Genres")
    plt.show()
    st.pyplot(fig)

    st.write(f"### Mel Spectrogram")
    st.image("melspectrogram.png", use_column_width=True)




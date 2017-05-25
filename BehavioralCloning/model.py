import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from keras.layers import Lambda, Conv2D, MaxPooling2D, Dropout, Dense, Flatten
from utils import INPUT_SHAPE, batch_generator
import argparse
import os

np.random.seed(0)


def read_DB(args):
    allPath = []
    allPath.append(args.data_dir+"/data2/data_db.txt")
    allPath.append(args.data_dir+"/data3/data_db.txt")
    allPath.append(args.data_dir+"/data4/data_db.txt")
    allPath.append(args.data_dir+"/data5/data_db.txt")
    allPath.append(args.data_dir+"/dataRetrig/data_db.txt")
    #allPath.append(args.data_dir+"/dataNew/data_db.txt")
    #allPath.append(args.data_dir+"/data6/data_db.txt")

    #path = os.path.join(args.data_dir,'data_db.txt')
    X = []
    Y = []
    for path in allPath:
        with open(path) as f:
            for line in f:
                tokens = line.split()
                X.append(tokens[0])
                steer = float(tokens[1])
                throttle = float(tokens[2])
                if (throttle>0.0) :
                    throttle = 1.0
                if (throttle<0.2):
                    throttle = -1.0
                #if (steer > 0.6): steer = 1.0
                #if (steer < -0.6): steer = -1.0
                Y.append("{0:.3f} {0:.3f}".format(steer,throttle))
    return X,Y


def load_data(args):
    """
    Load training data and split it into training and validation set
    """
    X,y = read_DB(args)

    X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=args.test_size, random_state=0)

    return X_train, X_valid, y_train, y_valid


def build_model(args):
    """
    Modified NVIDIA model
    """
    model = Sequential()
    model.add(Lambda(lambda x: x/127.5-1.0, input_shape=INPUT_SHAPE))
    model.add(Conv2D(24, 5, 5, activation='elu', subsample=(2, 2)))
    model.add(Conv2D(36, 5, 5, activation='elu', subsample=(2, 2)))
    model.add(Conv2D(48, 5, 5, activation='elu', subsample=(2, 2)))
    model.add(Conv2D(64, 3, 3, activation='elu'))
    model.add(Conv2D(64, 3, 3, activation='elu'))
    model.add(Dropout(args.keep_prob))
    model.add(Flatten())
    model.add(Dense(256, activation='elu'))
    model.add(Dense(128, activation='elu'))
    model.add(Dense(64, activation='elu'))
    model.add(Dropout(args.keep_prob))
    model.add(Dense(32, activation='elu'))
    model.add(Dense(2))
    model.summary()

    return model


def train_model(model, args, X_train, X_valid, y_train, y_valid):
    """
    Train the model
    """
    checkpoint = ModelCheckpoint('modelThrottle1-{val_loss:03f}.h5',
                                 monitor='val_loss',
                                 verbose=1,
                                 mode='auto')
                                 #save_best_only=args.save_best_only,
                                 

    model.compile(loss='mean_squared_error', optimizer=Adam(lr=args.learning_rate))

    model.fit_generator(batch_generator(args.data_dir, X_train, y_train, args.batch_size, True),
                        len(X_train),
                        nb_epoch=args.nb_epoch,
                        max_q_size=1,
                        validation_data=batch_generator(args.data_dir, X_valid, y_valid, args.batch_size, False),
                        nb_val_samples=len(X_valid),
                        callbacks=[checkpoint],
                        verbose=1)


def s2b(s):
    """
    Converts a string to boolean value
    """
    s = s.lower()
    return s == 'true' or s == 'yes' or s == 'y' or s == '1'


def main():
    """
    Load train/validation data set and train the model
    """
    parser = argparse.ArgumentParser(description='Behavioral Cloning Training Program')
    parser.add_argument('-d', help='data directory',        dest='data_dir',          type=str,   default='/home/andi/Desktop/Wi-FiRCCar/wifi-rc/dataSets')
    parser.add_argument('-t', help='test size fraction',    dest='test_size',         type=float, default=0.1)
    parser.add_argument('-k', help='drop out probability',  dest='keep_prob',         type=float, default=0.5)
    parser.add_argument('-n', help='number of epochs',      dest='nb_epoch',          type=int,   default=20)
    parser.add_argument('-s', help='samples per epoch',     dest='samples_per_epoch', type=int,   default=20000)
    parser.add_argument('-b', help='batch size',            dest='batch_size',        type=int,   default=200)
    parser.add_argument('-o', help='save best models only', dest='save_best_only',    type=s2b,   default='true')
    parser.add_argument('-l', help='learning rate',         dest='learning_rate',     type=float, default=1.0e-3)
    args = parser.parse_args()

    print('-' * 30)
    print('Parameters')
    print('-' * 30)
    for key, value in vars(args).items():
        print('{:<20} := {}'.format(key, value))
    print('-' * 30)

    data = load_data(args)
    model = build_model(args)
    train_model(model, args, *data)


if __name__ == '__main__':
    main()


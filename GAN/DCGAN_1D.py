import numpy as np
import tensorflow as tf
import pickle
import matplotlib.pyplot as plt
import scipy.io as scio


# from tensorflow.examples.tutorials.mnist import input_data
# mnist = input_data.read_data_sets('/tmp/data')

def get_random_block_form_data(data_sampls,batch_size):
    start_index=np.random.randint(0,len(data_sampls)-batch_size)
    return data_sampls[start_index:(start_index+batch_size)]

matdata=scio.loadmat("casewestern_bearing_Dataset.mat")
data=matdata['data']


def get_inputs(noise_dim, data_dim,data_depth):
    """
    @Author: Nelson Zhao
    --------------------
    :param noise_dim: 噪声图片的size
    :param image_height: 真实图像的height
    :param image_width: 真实图像的width
    :param image_depth: 真实图像的depth
    """
    inputs_real = tf.placeholder(tf.float32, [None, data_dim,data_depth], name='inputs_real')
    inputs_noise = tf.placeholder(tf.float32, [None, noise_dim], name='inputs_noise')

    return inputs_real, inputs_noise


def get_generator(noise_img, output_dim, is_train=True, alpha=0.01):
    """
    @Author: Nelson Zhao
    --------------------
    :param noise_img: 噪声信号，tensor类型
    :param output_dim: 生成图片的depth
    :param is_train: 是否为训练状态，该参数主要用于作为batch_normalization方法中的参数使用
    :param alpha: Leaky ReLU系数
    """

    with tf.variable_scope("generator", reuse=(not is_train)):
        # 100 x 1 to 4 x 4 x 512
        # 全连接层

        layer1 = tf.layers.dense(noise_img, 64* 256)
        layer1 = tf.reshape(layer1, [-1, 64, 256])
        # batch normalization
        layer1 = tf.layers.batch_normalization(layer1, training=is_train)
        # Leaky ReLU
        layer1 = tf.maximum(alpha * layer1, layer1)
        # dropout
        layer1 = tf.nn.dropout(layer1, keep_prob=0.8)



        # 4 x 4 x 512 to 7 x 7 x 256
        filter1=tf.get_variable(name="filter1",shape=[5,128,256],initializer=tf.truncated_normal_initializer(stddev=0.1))
        layer2=tf.contrib.nn.conv1d_transpose(layer1,filter1,output_shape=[64,128,128],stride=2,padding="SAME")
        # layer2 = tf.layers.conv2d_transpose(layer1, 256, 4, strides=2, padding='SAME')
        layer2 = tf.layers.batch_normalization(layer2, training=is_train)
        layer2 = tf.nn.leaky_relu(layer2,alpha=alpha)
        layer2 = tf.nn.dropout(layer2, keep_prob=0.8)


        # 256x1x256 to 512x1x128
        filter2=tf.get_variable(name='filter2',shape=[5,64,128],initializer=tf.truncated_normal_initializer(stddev=0.1))
        layer3=tf.contrib.nn.conv1d_transpose(layer2,filter2,output_shape=[64,256,64],stride=2,padding='SAME')
        # layer3 = tf.layers.conv2d_transpose(layer2, 128, 3, strides=2, padding='SAME')
        layer3 = tf.layers.batch_normalization(layer3, training=is_train)
        layer3 = tf.nn.leaky_relu(layer3,alpha=alpha)
        layer3 = tf.nn.dropout(layer3, keep_prob=0.8)


        # 512x1x128 to 1024 x 1x1
        filter3=tf.get_variable(name="filter3",shape=[11,output_dim,64])
        logits=tf.contrib.nn.conv1d_transpose(layer3,filter3,output_shape=[64,1024,output_dim],stride=4,padding='SAME')
        # logits = tf.layers.conv2d_transpose(layer3, output_dim, 3, strides=2, padding='SAME')
        # MNIST原始数据集的像素范围在0-1，这里的生成图片范围为(-1,1)
        # 因此在训练时，记住要把MNIST像素范围进行resize
        outputs = tf.tanh(logits)

        return outputs


def get_discriminator(inputs_img, reuse=False, alpha=0.01):
    """
    @Author: Nelson Zhao
    --------------------
    @param inputs_img: 输入图片，tensor类型
    @param alpha: Leaky ReLU系数
    """

    with tf.variable_scope("discriminator", reuse=reuse):
        # 28 x 28 x 1 to 14 x 14 x 128
        # 第一层不加入BN
        filter1=tf.get_variable(name='filter1',shape=[11,1,64],initializer=tf.truncated_normal_initializer(stddev=0.1))
        layer1=tf.nn.conv1d(inputs_img,filter1,stride=4,padding="SAME")
        # layer1 = tf.layers.conv2d(inputs_img, 128, 3, strides=2, padding='SAME')
        layer1 = tf.nn.leaky_relu(layer1,alpha=alpha)
        layer1 = tf.nn.dropout(layer1, keep_prob=0.8)

        # 14 x 14 x 128 to 7 x 7 x 256
        filter2 = tf.get_variable(name='filter2', shape=[5, 64, 128],
                                  initializer=tf.truncated_normal_initializer(stddev=0.1))
        layer2=tf.nn.conv1d(layer1,filter2,stride=2,padding="SAME")
        # layer2 = tf.layers.conv2d(layer1, 256, 3, strides=2, padding='SAME')
        layer2 = tf.layers.batch_normalization(layer2, training=True)
        layer2 = tf.nn.leaky_relu(layer2,alpha=alpha)
        layer2 = tf.nn.dropout(layer2, keep_prob=0.8)

        # 7 x 7 x 256 to 4 x 4 x 512
        filter3 = tf.get_variable(name='filter3', shape=[5, 128, 256],
                                  initializer=tf.truncated_normal_initializer(stddev=0.1))
        layer3 = tf.nn.conv1d(layer2, filter3, stride=2, padding="SAME")
        # layer3 = tf.layers.conv2d(layer2, 512, 3, strides=2, padding='SAME')
        layer3 = tf.layers.batch_normalization(layer3, training=True)
        layer3 = tf.nn.leaky_relu(layer3,alpha=alpha)
        layer3 = tf.nn.dropout(layer3, keep_prob=0.8)

        # 4 x 4 x 512 to 4*4*512 x 1
        flatten = tf.reshape(layer3, (-1, 64*256))
        logits = tf.layers.dense(flatten, 1)
        outputs = tf.sigmoid(logits)

        return logits, outputs


def get_loss(inputs_real, inputs_noise, image_depth, smooth=0.1):
    """
    @Author: Nelson Zhao
    --------------------
    @param inputs_real: 输入图片，tensor类型
    @param inputs_noise: 噪声图片，tensor类型
    @param image_depth: 图片的depth（或者叫channel）
    @param smooth: label smoothing的参数
    """

    g_outputs = get_generator(inputs_noise, image_depth, is_train=True)
    d_logits_real, d_outputs_real = get_discriminator(inputs_real)
    d_logits_fake, d_outputs_fake = get_discriminator(g_outputs, reuse=True)

    # 计算Loss
    g_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=d_logits_fake,
                                                                    labels=tf.ones_like(d_outputs_fake) * (1 - smooth)))

    d_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=d_logits_real,
                                                                         labels=tf.ones_like(d_outputs_real) * (
                                                                         1 - smooth)))
    d_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=d_logits_fake,
                                                                         labels=tf.zeros_like(d_outputs_fake)))
    d_loss = tf.add(d_loss_real, d_loss_fake)

    return g_loss, d_loss


def get_optimizer(g_loss, d_loss, beta1=0.4, learning_rate=0.001):
    """
    @Author: Nelson Zhao
    --------------------
    @param g_loss: Generator的Loss
    @param d_loss: Discriminator的Loss
    @learning_rate: 学习率
    """

    train_vars = tf.trainable_variables()

    g_vars = [var for var in train_vars if var.name.startswith("generator")]
    d_vars = [var for var in train_vars if var.name.startswith("discriminator")]

    # Optimizer
    with tf.control_dependencies(tf.get_collection(tf.GraphKeys.UPDATE_OPS)):
        g_opt = tf.train.AdamOptimizer(0.001, beta1=beta1).minimize(g_loss, var_list=g_vars)
        d_opt = tf.train.AdamOptimizer(0.001, beta1=beta1).minimize(d_loss, var_list=d_vars)

    return g_opt, d_opt

def plot_images(samples):
    fig, axes = plt.subplots(nrows=1, ncols=2, sharex=True, sharey=True, figsize=(50,2))
    x=np.arange(1024)
    for img, ax in zip(samples, axes):
        print(img.shape)
        ax.plot(x,img)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
    fig.tight_layout(pad=0)


def show_generator_output(sess, n_images, inputs_noise, output_dim):
    """
    @Author: Nelson Zhao
    --------------------
    @param sess: TensorFlow session
    @param n_images: 展示图片的数量
    @param inputs_noise: 噪声图片
    @param output_dim: 图片的depth（或者叫channel）
    @param image_mode: 图像模式：RGB或者灰度
    """
    cmap = 'Greys_r'
    noise_shape = inputs_noise.get_shape().as_list()[-1]
    # 生成噪声图片
    examples_noise = np.random.uniform(-0.61, 0.64, size=[n_images, noise_shape])

    samples = sess.run(get_generator(inputs_noise, output_dim, False),
                       feed_dict={inputs_noise: examples_noise})
    print(samples.shape)
    result = np.squeeze(samples, -1)
    print(result.shape)
    return result

# 定义参数
batch_size = 64
noise_size = 1024
epochs = 1000
n_samples = 2
learning_rate = 0.001
beta1 = 0.4


def train(noise_size, data_shape, batch_size, n_samples):
    """
    @Author: Nelson Zhao
    --------------------
    @param noise_size: 噪声size
    @param data_shape: 真实图像shape
    @batch_size:一次训练输入样本数量
    @n_samples: 显示示例图片数量
    """

    # 存储loss
    losses = []
    steps = 0

    inputs_real, inputs_noise = get_inputs(noise_size, data_shape[1], data_shape[2])#noise_size=100
    g_loss, d_loss = get_loss(inputs_real, inputs_noise, data_shape[-1])
    g_train_opt, d_train_opt = get_optimizer(g_loss, d_loss, beta1, learning_rate)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        # 迭代epoch
        for e in range(epochs):
            for batch_i in range(data.shape[0] // batch_size):
                steps += 1
                batch=get_random_block_form_data(data,batch_size)
                batch_images = batch.reshape((batch_size, data_shape[1], data_shape[2]))


                # noise
                batch_noise = np.random.uniform(-0.61, 0.64, size=(batch_size, noise_size))

                # run optimizer
                _ = sess.run(g_train_opt, feed_dict={inputs_real: batch_images,
                                                     inputs_noise: batch_noise})
                _ = sess.run(d_train_opt, feed_dict={inputs_real: batch_images,
                                                     inputs_noise: batch_noise})

                if steps % 10== 0:
                    train_loss_d = d_loss.eval({inputs_real: batch_images,
                                                inputs_noise: batch_noise})
                    train_loss_g = g_loss.eval({inputs_real: batch_images,
                                                inputs_noise: batch_noise})
                    losses.append((train_loss_d, train_loss_g))
                    # 显示图片
                    # samples = show_generator_output(sess, n_samples, inputs_noise, data_shape[-1])
                    # plot_images(samples)
                    # plt.show()
                    print("Epoch {}/{}....".format(e + 1, epochs),
                          "Discriminator Loss: {:.4f}....".format(train_loss_d),
                          "Generator Loss: {:.4f}....".format(train_loss_g))


with tf.Graph().as_default():
    train(noise_size, [-1, 1024, 1], batch_size, n_samples)
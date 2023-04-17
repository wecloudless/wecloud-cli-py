# train.py
#!/usr/bin/env	python3

""" train network using pytorch

author baiyu
"""

import os
import sys
import argparse
import time
from datetime import datetime
import logging

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.INFO)

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms

from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from conf import settings
from utils import get_network, get_training_dataloader, get_test_dataloader, WarmUpLR, \
    most_recent_folder, most_recent_weights, last_epoch, best_acc_weights

import wecloud_callback

logger = logging.Logger(__name__)

def train(inputs, targets):
    if args.gpu:
        targets = targets.cuda()
        inputs = inputs.cuda()
    optimizer.zero_grad()
    outputs = net(inputs)
    loss = loss_function(outputs, targets)
    loss.backward()
    optimizer.step()
    return loss, outputs


def wecloud_train(epoch):

    start = time.time()
    net.train()
    epoch_start_time = time.time()
    for batch_index, (images, labels) in enumerate(cifar100_training_loader):
        wecloud_callback.step_begin()
        batch_start_time = time.time()

        loss, outputs = train(images, labels)

        n_iter = (epoch - 1) * len(cifar100_training_loader) + batch_index + 1

        last_layer = list(net.children())[-1]
        for name, para in last_layer.named_parameters():
            if 'weight' in name:
                writer.add_scalar('LastLayerGradients/grad_norm2_weights', para.grad.norm(), n_iter)
            if 'bias' in name:
                writer.add_scalar('LastLayerGradients/grad_norm2_bias', para.grad.norm(), n_iter)

        # logging.info('Training Epoch: {epoch} [{trained_samples}/{total_samples}]\tLoss: {:0.4f}\tLR: {:0.6f}'.format(
        #     loss.item(),
        #     optimizer.param_groups[0]['lr'],
        #     epoch=epoch,
        #     trained_samples=batch_index * args.b + len(images),
        #     total_samples=len(cifar100_training_loader.dataset)
        # ))
        csv_writer.write("{},{},{},{},{},{},{}".format(
            epoch,                                  # epoch
            n_iter,                                 # iteration
            batch_index * args.b + len(images),     # trained_samples
            len(cifar100_training_loader.dataset),  # total_samples
            loss.item(),                            # loss
            optimizer.param_groups[0]['lr'],        # lr
            time.time() - epoch_start_time,         # current epoch wall-clock time
        ))
        logging.info("epoch = {}, iteration = {}, trained_samples = {}, total_samples = {}, loss = {}, lr = {}, current_epoch_wall-clock_time = {}".format(
            epoch,                                  # epoch
            n_iter,                                 # iteration
            batch_index * args.b + len(images),     # trained_samples
            len(cifar100_training_loader.dataset),  # total_samples
            loss.item(),                            # loss
            optimizer.param_groups[0]['lr'],        # lr
            time.time() - epoch_start_time,         # current epoch wall-clock time
        ))
        if args.profiling:
            logging.info(f"PROFILING: dataset total number {len(cifar100_training_loader.dataset)}, training one batch costs {time.time() - batch_start_time} seconds")
            return

        #update training loss for each iteration
        writer.add_scalar('Train/loss', loss.item(), n_iter)

        if epoch <= args.warm:
            warmup_scheduler.step()
        wecloud_callback.step_end()

    for name, param in net.named_parameters():
        layer, attr = os.path.splitext(name)
        attr = attr[1:]
        writer.add_histogram("{}/{}".format(layer, attr), param, epoch)

    finish = time.time()

    logging.info('epoch {} training time consumed: {:.2f}s'.format(epoch, finish - start))

@torch.no_grad()
def eval_training(epoch=0, tb=True):

    start = time.time()
    net.eval()

    test_loss = 0.0 # cost function error
    correct = 0.0

    for (images, labels) in cifar100_test_loader:

        if args.gpu:
            images = images.cuda()
            labels = labels.cuda()

        outputs = net(images)
        loss = loss_function(outputs, labels)

        test_loss += loss.item()
        _, preds = outputs.max(1)
        correct += preds.eq(labels).sum()

    finish = time.time()
    if args.gpu:
        logging.info('GPU INFO.....')
        logging.info(torch.cuda.memory_summary())
    logging.info('Evaluating Network.....')
    logging.info('Test set: Epoch: {}, Average loss: {:.4f}, Accuracy: {:.4f}, Time consumed:{:.2f}s'.format(
        epoch,
        test_loss / len(cifar100_test_loader.dataset),
        correct.float() / len(cifar100_test_loader.dataset),
        finish - start
    ))

    #add informations to tensorboard
    if tb:
        writer.add_scalar('Test/Average loss', test_loss / len(cifar100_test_loader.dataset), epoch)
        writer.add_scalar('Test/Accuracy', correct.float() / len(cifar100_test_loader.dataset), epoch)

    return correct.float() / len(cifar100_test_loader.dataset)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--net', type=str, required=True, help='net type')
    parser.add_argument('--gpu', action='store_true', default=False, help='use gpu or not')
    parser.add_argument('-b', type=int, default=128, help='batch size for dataloader')
    parser.add_argument('--epoch', type=int, default=100, help='num of epochs to train')
    parser.add_argument('--warm', type=int, default=1, help='warm up training phase')
    parser.add_argument('--lr', type=float, default=0.1, help='initial learning rate')
    parser.add_argument('--resume', action='store_true', default=False, help='resume training')
    parser.add_argument('--profiling', action="store_true", default=False, help="profile one batch")
    args = parser.parse_args()

    net = get_network(args)

    #data preprocessing:
    cifar100_training_loader = get_training_dataloader(
        settings.CIFAR100_TRAIN_MEAN,
        settings.CIFAR100_TRAIN_STD,
        num_workers=4,
        batch_size=args.b,
        shuffle=True
    )

    cifar100_test_loader = get_test_dataloader(
        settings.CIFAR100_TRAIN_MEAN,
        settings.CIFAR100_TRAIN_STD,
        num_workers=4,
        batch_size=args.b,
        shuffle=True
    )

    # log_header = ["epoch", "trained_samples", "total_samples", "loss", "lr", "current epoch wall-clock time"]
    os.makedirs(os.path.join("logs", args.net), exist_ok=True)
    csv_path = os.path.join("logs", args.net, f"{settings.TIME_NOW}.csv")
    csv_writer = open(csv_path, "w")
    csv_writer.write("epoch,iteration,trained_samples,total_samples,loss,lr,current epoch wall-clock time\n")


    loss_function = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4)
    train_scheduler = optim.lr_scheduler.MultiStepLR(optimizer, milestones=settings.MILESTONES, gamma=0.2) #learning rate decay
    iter_per_epoch = len(cifar100_training_loader)
    warmup_scheduler = WarmUpLR(optimizer, iter_per_epoch * args.warm)

    if args.resume:
        recent_folder = most_recent_folder(os.path.join(settings.CHECKPOINT_PATH, args.net), fmt=settings.DATE_FORMAT)
        if not recent_folder:
            raise Exception('no recent folder were found')

        checkpoint_path = os.path.join(settings.CHECKPOINT_PATH, args.net, recent_folder)

    else:
        checkpoint_path = os.path.join(settings.CHECKPOINT_PATH, args.net, settings.TIME_NOW)

    #use tensorboard
    if not os.path.exists(settings.LOG_DIR):
        os.mkdir(settings.LOG_DIR)

    #since tensorboard can't overwrite old values
    #so the only way is to create a new tensorboard log
    writer = SummaryWriter(log_dir=os.path.join(
            settings.LOG_DIR, args.net, settings.TIME_NOW))
    input_tensor = torch.Tensor(1, 3, 32, 32)
    if args.gpu:
        input_tensor = input_tensor.cuda()
    writer.add_graph(net.module if torch.cuda.device_count() > 1 else net, input_tensor)

    #create checkpoint folder to save model
    if not os.path.exists(checkpoint_path):
        os.makedirs(checkpoint_path)
    checkpoint_path = os.path.join(checkpoint_path, '{net}-{epoch}-{type}.pth')

    best_acc = 0.0
    if args.resume:
        best_weights = best_acc_weights(os.path.join(settings.CHECKPOINT_PATH, args.net, recent_folder))
        if best_weights:
            weights_path = os.path.join(settings.CHECKPOINT_PATH, args.net, recent_folder, best_weights)
            logging.info('found best acc weights file:{}'.format(weights_path))
            logging.info('load best training file to test acc...')
            net.load_state_dict(torch.load(weights_path))
            best_acc = eval_training(tb=False)
            logging.info('best acc is {:0.2f}'.format(best_acc))

        recent_weights_file = most_recent_weights(os.path.join(settings.CHECKPOINT_PATH, args.net, recent_folder))
        if not recent_weights_file:
            raise Exception('no recent weights file were found')
        weights_path = os.path.join(settings.CHECKPOINT_PATH, args.net, recent_folder, recent_weights_file)
        logging.info('loading weights file {} to resume training.....'.format(weights_path))
        net.load_state_dict(torch.load(weights_path))

        resume_epoch = last_epoch(os.path.join(settings.CHECKPOINT_PATH, args.net, recent_folder))

    wecloud_callback.init(
        total_steps=args.epoch * iter_per_epoch
    )
    for epoch in range(1, args.epoch + 1):
        if epoch > args.warm:
            train_scheduler.step(epoch)

        if args.resume:
            if epoch <= resume_epoch:
                continue

        wecloud_train(epoch)
        
        if args.profiling:
            break

        acc = eval_training(epoch)

        #start to save best performance model after learning rate decay to 0.01
        if epoch > settings.MILESTONES[1] and best_acc < acc:
            weights_path = checkpoint_path.format(net=args.net, epoch=epoch, type='best')
            logging.info('saving weights file to {}'.format(weights_path))
            torch.save(net.state_dict(), weights_path)
            best_acc = acc
            continue

        if not epoch % settings.SAVE_EPOCH:
            weights_path = checkpoint_path.format(net=args.net, epoch=epoch, type='regular')
            logging.info('saving weights file to {}'.format(weights_path))
            torch.save(net.state_dict(), weights_path)

    writer.close()
    csv_writer.close()
    # df = pd.DataFrame(all_log, columns=log_header)
    # os.makedirs(os.path.join("logs", args.net), exist_ok=True)
    # df.to_csv(os.path.join("logs", args.net, f"{settings.TIME_NOW}.csv"))


from tqdm import tqdm
from typing import Dict, Any, Optional
from run_manager import RunManager
import utils
import torch
from torch import nn
from torch.utils.data import DataLoader
from torch.optim import Optimizer


def train_step(model: nn.Module,
               dataloader: DataLoader,
               loss_fn: nn.modules.loss._Loss,
               optimizer: Optimizer,
               k_top: int,
               run_manager: RunManager,
               log_interval: int,
               epoch: int,
               device: str) -> dict[str, float]:
    model.train()
    train_loss = 0
    num_correct = 0
    num_predictions = 0

    for batch, (X, y) in tqdm(enumerate(dataloader), total=len(dataloader), desc="Train Step", leave=False):

        X, y = X.to(device), y.to(device)

        y_pred = model(X)

        loss = loss_fn(y_pred, y)
        train_loss += loss.item()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        num_correct += utils.count_top_k_correct(y_pred, y, k_top)
        num_predictions += len(y)

        if batch != 0 and batch % log_interval == 0:
            run_manager.log_metrics({"train/loss": loss.item(),
                                     "train/accuracy": num_correct / num_predictions}, epoch + batch / len(dataloader))

    train_loss = train_loss/len(dataloader)
    top_k_accuracy = num_correct / num_predictions

    return {"loss": train_loss, "top_k_accuracy": top_k_accuracy}


def test_step(model: nn.Module,
              dataloader: DataLoader,
              loss_fn: nn.modules.loss._Loss,
              k_top: int,
              run_manager: RunManager,
              log_interval: int,
              epoch: int,
              device: str) -> dict[str, float]:

    model.eval()

    test_loss = 0
    num_correct = 0
    num_predictions = 0

    with torch.inference_mode():

        for batch, (X, y) in tqdm(enumerate(dataloader), total=len(dataloader), desc="Test Step", leave=False):
            X, y = X.to(device), y.to(device)

            test_pred_logits = model(X)

            loss = loss_fn(test_pred_logits, y)
            test_loss += loss.item()

            num_correct += utils.count_top_k_correct(
                test_pred_logits, y, k_top)
            num_predictions += len(y)

            if batch != 0 and batch % log_interval == 0:
                run_manager.log_metrics({"val/loss": loss.item(),
                                         "val/accuracy": num_correct / num_predictions}, epoch + batch / len(dataloader))

    test_loss = test_loss / len(dataloader)
    top_k_accuracy = num_correct / num_predictions

    return {"loss": test_loss, "top_k_accuracy": top_k_accuracy}


def train(model: torch.nn.Module,
          train_dataloader: DataLoader,
          val_dataloader: DataLoader,
          optimizer: Optimizer,
          loss_fn: nn.modules.loss._Loss,
          epoch_start: int,
          epoch_end: int,
          k_top: int,
          run_manager: RunManager,
          checkpoint_interval: int,
          log_interval: int,
          device: str):
    """
    Train a PyTorch model.

    Args:
        model: A PyTorch model to train.
        train_dataloader: A PyTorch DataLoader for training data.
        val_dataloader: A PyTorch DataLoader for validation data.
        optimizer: A PyTorch optimizer to use for training.
        loss_fn: A PyTorch loss function to use for training.
        epoch_start: The starting epoch for training.
        epoch_end: The ending epoch for training.
        k_top: The value of k for top-k accuracy calculation.
        run_manager: An instance of the RunManager class for logging metrics.
        checkpoint_interval: The interval at which to save model checkpoints.
        log_interval: The interval at which to log metrics.
        device: The device to run the model on.

    """

    for epoch in tqdm(range(epoch_start, epoch_end), desc="Epochs"):

        train_step_dict = train_step(
            model, train_dataloader, loss_fn, optimizer, k_top, run_manager, log_interval, epoch, device)
        val_step_dict = test_step(
            model, val_dataloader, loss_fn, k_top, run_manager, log_interval, epoch, device)

        run_manager.log_metrics({"train/loss": train_step_dict["loss"],
                                 "val/loss": val_step_dict["loss"],
                                 "train/accuracy": train_step_dict["top_k_accuracy"],
                                 "val/accuracy": val_step_dict["top_k_accuracy"]}, epoch+1)

        if epoch != 0 and (epoch % checkpoint_interval == 0 or epoch == epoch_end - 1):
            run_manager.save_model(model, epoch)

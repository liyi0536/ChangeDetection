import os

import torch
import torchvision
import matplotlib.image as mpimg

from .metric import get_metric


def eval_model(
    model,
    data_loader,
    cfg,
    writer=None,
    step=0,
    criterion = None,
    save_imgs = False,
):
    device = cfg.MODEL.DEVICE
    model = model.to(device).eval()
    metric_all = dict(zip(
        cfg.EVAL.METRIC,
        [0.0] * len(cfg.EVAL.METRIC)
    ))
    with torch.no_grad():
        loss_all = 0.0
        for batch, data in enumerate(data_loader):
            img1, img2, gt = [img.to(device) for img in data]
            output = model(img1, img2)
            if criterion:
                loss = criterion(output,gt)
                loss_all += loss.item()
            out_tensor = torch.argmax(output, dim=1, keepdim=True).type_as(output)
            gt_tensor = gt[:, 1, :, :]
            metric = get_metric(out_tensor, gt_tensor)
            metric_all = add_metric(metric_all,metric)
            if save_imgs:
                save_output_imgs(cfg,metric,out_tensor)

        metric_avg = {k : v/data_loader.__len__() for k,v in metric_all.items()}
    if writer and criterion:
        writer.add_scalar("test/loss", loss_all/data_loader.__len__(), step)
        

    model = model.train()
    return metric_avg


def add_metric(ma,mb):
    """ma = ma + mb"""
    assert set(ma.keys()).issubset(mb.keys())
    for k,v in ma.items():
        ma[k] = mb[k] + v
    return ma

def save_output_imgs(cfg,metric,out_tensor):
    save_name = "_".join(["%s_%.3f"%(key,metric[key]) for key in cfg.EVAL.METRIC])+".png"
    grid = torchvision.utils.make_grid(out_tensor,padding=0,nrow=1,pad_value=1.0)
    image = grid.cpu().numpy().transpose((1,2,0))
    mpimg.imsave(os.path.join(cfg.EVAL.SAVE_IMAGE_ROOT, save_name),image)
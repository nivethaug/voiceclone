@property
def deepspeed_config(self):
    return {
        "train_micro_batch_size_per_gpu": self.batch_size_per_gpu,
        "optimizer": {
            "type": "Adam",
            "params": {"lr": float(self.min_lr)},
        },
        "scheduler": {
            "type": "WarmupDecayLR",
            "params": {
                "warmup_min_lr": float(self.min_lr),
                "warmup_max_lr": float(self.max_lr),
                "warmup_num_steps": self.warmup_steps,
                "total_num_steps": self.max_steps,
                "warmup_type": "linear",
            },
        },
        "gradient_clipping": self.gradient_clipping,
    }

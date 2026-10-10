"""Original CLASS target repaired as CTG-pattern research; no preterm outcome is fabricated."""
def train_preterm_guard(*args,**kwargs):
    from scripts.train_ctg_patterns import train
    return train()
if __name__=="__main__": train_preterm_guard()

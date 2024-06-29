import random

def perturb_random_number_generator(stored_state, random_number_generator):
    """Change state of random number generator to new random state"""
    random.seed(random.uniform(0,2000000))
    random_number_generator.setstate(random.getstate())
    stored_state = random_number_generator.getstate()

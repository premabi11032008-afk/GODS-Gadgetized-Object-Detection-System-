from ultralytics import YOLO
import os

def train_model():
    model = YOLO('runs/detect/road_damage_v1/weights/last.pt')

    # Start training!
    # YOLOv8 automatically uses Early Stopping by default if validation metrics don't improve.
    # The 'patience' parameter controls how many epochs to wait before stopping.
    print("Starting Training...")
    results = model.train(
        data=r'c:\Users\HAPPY\NEW PROJECTS\DT PROJECTS\DT PROJECT  2\dataset\data.yaml',
        resume=True,
        epochs=100,           # Maximum number of epochs
        patience=15,          # Early Stopping: Stop if no improvement after 15 epochs
        imgsz=640,            # Image size
        batch=16,             # Batch size (reduce to 8 or 4 if your computer runs out of memory)
        name='road_damage_v1',# Name of the output folder in runs/detect/
        device='',            # Leave empty to auto-select GPU if available, else CPU
        
        # Advanced Hyperparameter Tuning:
        optimizer='AdamW',    # AdamW is often better for this kind of specific fine-tuning
        lr0=0.001,            # Initial learning rate
        cos_lr=True,          # Cosine learning rate scheduling (helps smooth out learning)
        dropout=0.1,          # Helps prevent overfitting
        
        # Augmentations (to make the model more robust)
        fliplr=0.5,           # 50% chance to flip images left-right
        mosaic=1.0,           # Mosaic augmentation helps detect small objects (like far away potholes)
        mixup=0.1             # Mixes images together slightly to improve robustness
    )
    
    print("Training Complete! The best model weights are saved in 'runs/detect/road_damage_v1/weights/best.pt'")

def tune_hyperparameters():
    """
    WARNING: Hyperparameter tuning takes a VERY long time (often days on a single GPU).
    If you want YOLO to automatically find the perfect hyperparameters using Ray Tune,
    run this function instead of train_model().
    """
    model = YOLO('yolov8n.pt')
    
    # This will run 30 different experiments to find the best hyperparameters
    model.tune(
        data=r'c:\Users\HAPPY\NEW PROJECTS\DT PROJECTS\DT PROJECT  2\dataset\data.yaml',
        epochs=30,
        iterations=30,
        optimizer='AdamW',
        plots=False,
        save=False,
        val=False
    )

if __name__ == '__main__':
    # We will just run the standard training by default, which includes our manual hyperparameter settings
    train_model()

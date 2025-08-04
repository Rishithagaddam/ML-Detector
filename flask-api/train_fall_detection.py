#!/usr/bin/env python3
"""
Train YOLOv5 model for fall detection

Usage:
    python train_fall_detection.py --epochs 100 --batch-size 16 --img 640

This script trains a YOLOv5 model specifically for fall detection using the prepared dataset.
"""

import sys
import os
from pathlib import Path
import argparse

# Add the yolov5 directory to the Python path
current_dir = Path(__file__).resolve().parent
yolov5_dir = current_dir.parent / "yolov5"
sys.path.insert(0, str(yolov5_dir))

def parse_arguments():
    """Parse command line arguments for fall detection training."""
    parser = argparse.ArgumentParser(description='Train YOLOv5 for Fall Detection')
    
    # Training parameters
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size for training')
    parser.add_argument('--img', '--img-size', type=int, default=640, help='Image size for training')
    parser.add_argument('--device', default='', help='Device to use (cuda device or cpu)')
    parser.add_argument('--workers', type=int, default=8, help='Number of data loading workers')
    
    # Model parameters
    parser.add_argument('--weights', type=str, default='yolov5s.pt', 
                       help='Initial weights path (default: yolov5s.pt)')
    parser.add_argument('--cfg', type=str, default='', 
                       help='Model configuration file (default: auto-detect from weights)')
    
    # Advanced parameters
    parser.add_argument('--resume', nargs='?', const=True, default=False, 
                       help='Resume most recent training')
    parser.add_argument('--name', default='fall_detection', help='Save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='Existing project/name ok')
    parser.add_argument('--cache', type=str, nargs='?', const='ram', 
                       help='Image cache (disk, ram, or disabled)')
    
    return parser.parse_args()

def main():
    """Main training function for fall detection."""
    args = parse_arguments()
    
    # Set up paths
    data_yaml = current_dir / "models" / "roboflow" / "fall-detection" / "fall_detection.yaml"
    project_dir = current_dir.parent / "yolov5" / "runs" / "train"
    
    # Ensure data file exists
    if not data_yaml.exists():
        print(f"Error: Data configuration file not found: {data_yaml}")
        print("Please ensure the fall detection dataset is properly set up.")
        return
    
    print("="*60)
    print("FALL DETECTION MODEL TRAINING")
    print("="*60)
    print(f"Dataset: {data_yaml}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch Size: {args.batch_size}")
    print(f"Image Size: {args.img}")
    print(f"Initial Weights: {args.weights}")
    print(f"Device: {args.device if args.device else 'auto-detect'}")
    print("="*60)
    
    # Change to yolov5 directory for training
    original_cwd = os.getcwd()
    os.chdir(yolov5_dir)
    
    try:
        # Import YOLOv5 training after changing directory
        from train import main as train_main, parse_opt
        
        # Create a mock argument list for YOLOv5
        sys.argv = [
            'train.py',
            '--data', str(data_yaml),
            '--epochs', str(args.epochs),
            '--batch-size', str(args.batch_size),
            '--img', str(args.img),
            '--weights', args.weights,
            '--device', args.device,
            '--workers', str(args.workers),
            '--project', str(project_dir),
            '--name', args.name,
            '--cache', args.cache if args.cache else 'ram',
        ]
        
        if args.cfg:
            sys.argv.extend(['--cfg', args.cfg])
        
        if args.resume:
            sys.argv.append('--resume')
        
        if args.exist_ok:
            sys.argv.append('--exist-ok')
        
        # Parse YOLOv5 options
        opt = parse_opt()
        
        # Run training with the parsed options
        train_main(opt)
        
        print("\n" + "="*60)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Model saved in: {project_dir / args.name}")
        print("The trained model can be found in the 'weights' subdirectory.")
        print("Use 'best.pt' for inference and 'last.pt' to resume training.")
        
    except Exception as e:
        print(f"\nTraining failed with error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Return to original directory
        os.chdir(original_cwd)

if __name__ == "__main__":
    main()

"""Quick retraining script with all accuracy improvements.

This script retrains the model with:
- Label smoothing (prevents single-class prediction)
- Stronger regularization (L2=0.02, higher dropout)
- Lower learning rates (5e-4 initial, 1e-5 fine-tuning)
- Larger images (299x299)
- Enhanced augmentation
- Better architecture (256+128 neurons)

Usage:
    python quick_retrain.py
"""
from pathlib import Path
from src.models.model_training import train_pill_model

def main():
    print("="*80)
    print("RETRAINING MODEL WITH ANTI-OVERFITTING IMPROVEMENTS")
    print("="*80)
    print("\nKey Features:")
    print("  ✓ Label smoothing (0.1) - prevents overconfident single-class predictions")
    print("  ✓ Stronger regularization (L2=0.02, dropout 0.6/0.5/0.4)")
    print("  ✓ Lower learning rates (5e-4 → 1e-5)")
    print("  ✓ Enhanced augmentation (rotation, zoom, translation)")
    print("  ✓ Larger images (299x299)")
    print("  ✓ Better architecture (256+128 dense layers)")
    print("  ✓ 50 epochs per phase with adaptive LR")
    print("\n" + "="*80)
    
    # Check dataset
    dataset_path = Path("data/pills_dataset")
    if not dataset_path.exists():
        print(f"\n❌ ERROR: Dataset not found at {dataset_path}")
        print("Please ensure your dataset is in data/pills_dataset/")
        return
    
    # Count classes
    num_classes = len([d for d in dataset_path.iterdir() if d.is_dir()])
    print(f"\n📊 Found {num_classes} medication classes")
    
    # Warn about small dataset
    if num_classes < 14:
        print(f"⚠️  WARNING: Only {num_classes} classes found (expected 14)")
    
    print("\n🚀 Starting training...")
    print("This will take approximately 60-90 minutes with GPU")
    print("Press Ctrl+C to cancel\n")
    
    try:
        result = train_pill_model(
            epochs_frozen=50,
            epochs_finetune=50,
            fine_tune_at=100
        )
        
        print("\n" + "="*80)
        print("✅ TRAINING COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"\nFinal Metrics:")
        print(f"  Test Accuracy: {result.metrics.get('accuracy', 'N/A')}")
        print(f"  Classes: {len(result.labels)}")
        print(f"\n📁 Model saved to: models/trained_models/pill_mobilenetv2.keras")
        print(f"📁 Labels saved to: models/trained_models/pill_mobilenetv2_labels.json")
        
        # Show per-class metrics if available
        if 'per_class' in result.metrics:
            print("\n📊 Per-Class Results:")
            for cls_name, metrics in result.metrics['per_class'].items():
                acc = metrics.get('accuracy', 0)
                print(f"  {cls_name}: {acc*100:.1f}%")
        
        print("\n💡 Next Steps:")
        print("  1. Restart Flask server: python run.py")
        print("  2. Test predictions with different pill images")
        print("  3. If still overfitting, collect more training images (50-100 per class)")
        print("\n" + "="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training cancelled by user")
    except Exception as e:
        print(f"\n\n❌ ERROR during training: {e}")
        print("Check the error message above for details")
        raise

if __name__ == "__main__":
    main()

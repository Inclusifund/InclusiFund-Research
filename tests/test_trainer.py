"""Tests for the training loop."""

from quantum_grants.training.trainer import train, TrainingConfig


class TestTrainingConfig:
    def test_defaults(self):
        config = TrainingConfig()
        assert config.n_layers == 2
        assert config.n_epochs > 0
        assert config.batch_size > 0


class TestTrain:
    def test_returns_logs(self):
        config = TrainingConfig(
            n_layers=1,
            n_epochs=3,
            batch_size=8,
            n_grants=3,
            n_applicants=5,
            seed=42,
        )
        logs = train(config)
        assert len(logs) == 3

    def test_log_has_required_fields(self):
        config = TrainingConfig(
            n_layers=1,
            n_epochs=2,
            batch_size=8,
            n_grants=3,
            n_applicants=5,
            seed=42,
        )
        logs = train(config)
        for log in logs:
            assert hasattr(log, "epoch")
            assert hasattr(log, "loss")
            assert hasattr(log, "accuracy")
            assert 0 <= log.accuracy <= 1

    def test_loss_decreases_or_stable(self):
        config = TrainingConfig(
            n_layers=1,
            learning_rate=0.1,
            n_epochs=5,
            batch_size=16,
            n_grants=5,
            n_applicants=10,
            seed=42,
        )
        logs = train(config)
        # Loss at end should be <= loss at start (or close)
        # Allow 10% tolerance for noisy training
        assert logs[-1].loss <= logs[0].loss * 1.1

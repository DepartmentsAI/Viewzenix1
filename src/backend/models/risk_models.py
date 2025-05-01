"""
Risk Management Models

This module defines the data models for risk management, including:
- Risk parameters (stop-loss/take-profit settings, position limits)
- Risk metrics (current exposure, portfolio statistics)
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class StopLossTakeProfitSettings:
    """Settings for stop-loss and take-profit functionality."""
    # Whether SL/TP is enabled for orders
    enabled: bool = True
    
    # Stop-loss percentage (e.g., 0.02 for 2%)
    stop_loss_percent: float = 0.02
    
    # Take-profit percentage (e.g., 0.05 for 5%)
    take_profit_percent: float = 0.05
    
    # Whether to use fixed price instead of percentage
    use_fixed_price: bool = False
    
    # Fixed price values (only used if use_fixed_price is True)
    fixed_stop_loss_price: Optional[float] = None
    fixed_take_profit_price: Optional[float] = None
    
    # Whether to calculate SL/TP based on fill price vs order price
    use_fill_price_for_sl_tp: bool = True


@dataclass
class PortfolioProtectionSettings:
    """Settings for portfolio-wide risk management."""
    # Whether portfolio protection is enabled
    enabled: bool = True
    
    # Maximum daily drawdown allowed (as a percentage, e.g., 0.05 for 5%)
    max_daily_drawdown_percent: float = 0.05
    
    # Maximum number of open positions allowed
    max_open_positions: int = 10
    
    # Maximum percentage of account equity for a single position
    max_position_size_percent: float = 0.05
    
    # Base account equity for calculating absolute thresholds
    base_equity: float = 10000.0


@dataclass
class CleanupSettings:
    """Settings for orphaned order cleanup service."""
    # Whether automatic cleanup is enabled
    enabled: bool = True
    
    # Age threshold in hours for considering orders orphaned
    orphaned_order_age_hours: int = 24
    
    # Cleanup interval in seconds
    cleanup_interval_seconds: int = 3600


@dataclass
class RiskParameters:
    """Combined risk management parameters."""
    sl_tp: StopLossTakeProfitSettings = field(default_factory=StopLossTakeProfitSettings)
    portfolio: PortfolioProtectionSettings = field(default_factory=PortfolioProtectionSettings)
    cleanup: CleanupSettings = field(default_factory=CleanupSettings)
    
    # Additional risk parameters can be added here as needed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary for JSON serialization."""
        return {
            "sl_tp": {
                "enabled": self.sl_tp.enabled,
                "stop_loss_percent": self.sl_tp.stop_loss_percent,
                "take_profit_percent": self.sl_tp.take_profit_percent,
                "use_fixed_price": self.sl_tp.use_fixed_price,
                "fixed_stop_loss_price": self.sl_tp.fixed_stop_loss_price,
                "fixed_take_profit_price": self.sl_tp.fixed_take_profit_price,
                "use_fill_price_for_sl_tp": self.sl_tp.use_fill_price_for_sl_tp
            },
            "portfolio": {
                "enabled": self.portfolio.enabled,
                "max_daily_drawdown_percent": self.portfolio.max_daily_drawdown_percent,
                "max_open_positions": self.portfolio.max_open_positions,
                "max_position_size_percent": self.portfolio.max_position_size_percent,
                "base_equity": self.portfolio.base_equity
            },
            "cleanup": {
                "enabled": self.cleanup.enabled,
                "orphaned_order_age_hours": self.cleanup.orphaned_order_age_hours,
                "cleanup_interval_seconds": self.cleanup.cleanup_interval_seconds
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskParameters':
        """Create RiskParameters from a dictionary."""
        sl_tp_data = data.get("sl_tp", {})
        portfolio_data = data.get("portfolio", {})
        cleanup_data = data.get("cleanup", {})
        
        return cls(
            sl_tp=StopLossTakeProfitSettings(
                enabled=sl_tp_data.get("enabled", True),
                stop_loss_percent=sl_tp_data.get("stop_loss_percent", 0.02),
                take_profit_percent=sl_tp_data.get("take_profit_percent", 0.05),
                use_fixed_price=sl_tp_data.get("use_fixed_price", False),
                fixed_stop_loss_price=sl_tp_data.get("fixed_stop_loss_price"),
                fixed_take_profit_price=sl_tp_data.get("fixed_take_profit_price"),
                use_fill_price_for_sl_tp=sl_tp_data.get("use_fill_price_for_sl_tp", True)
            ),
            portfolio=PortfolioProtectionSettings(
                enabled=portfolio_data.get("enabled", True),
                max_daily_drawdown_percent=portfolio_data.get("max_daily_drawdown_percent", 0.05),
                max_open_positions=portfolio_data.get("max_open_positions", 10),
                max_position_size_percent=portfolio_data.get("max_position_size_percent", 0.05),
                base_equity=portfolio_data.get("base_equity", 10000.0)
            ),
            cleanup=CleanupSettings(
                enabled=cleanup_data.get("enabled", True),
                orphaned_order_age_hours=cleanup_data.get("orphaned_order_age_hours", 24),
                cleanup_interval_seconds=cleanup_data.get("cleanup_interval_seconds", 3600)
            )
        )


@dataclass
class RiskMetrics:
    """Current risk metrics for monitoring portfolio state."""
    # Current account equity
    current_equity: float = 0.0
    
    # Starting equity for day (for drawdown calculation)
    starting_equity: float = 0.0
    
    # Current drawdown percentage
    current_drawdown_percent: float = 0.0
    
    # Number of currently open positions
    open_position_count: int = 0
    
    # Total exposure as percentage of equity
    total_exposure_percent: float = 0.0
    
    # List of position sizes in percentage of equity
    position_sizes: List[float] = field(default_factory=list)
    
    # Timestamp of last update
    last_updated: Optional[float] = None 
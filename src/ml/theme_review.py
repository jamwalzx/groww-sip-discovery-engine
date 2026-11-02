import logging
from typing import Optional, Dict, Any, List
from src.db.database import get_db
from src.db.models import Theme, ItemThemeMapping

logger = logging.getLogger("ml.theme_review")

class ThemeReviewManager:
    """
    Human-in-the-loop review interface allowing Product Managers to
    inspect, rename, merge overlapping clusters, or split mixed clusters.
    """

    @staticmethod
    def get_all_themes() -> List[Dict[str, Any]]:
        """Returns all discovered themes with item counts and exemplar quotes."""
        with get_db() as db:
            themes = db.query(Theme).order_by(Theme.item_count.desc()).all()
            return [t.to_dict() for t in themes]

    @staticmethod
    def rename_theme(theme_id: str, new_title: str, new_description: Optional[str] = None) -> bool:
        """Renames an existing theme and optionally updates its description."""
        with get_db() as db:
            theme = db.query(Theme).filter(Theme.id == theme_id).first()
            if not theme:
                logger.warning(f"Theme {theme_id} not found.")
                return False
            theme.title = new_title.strip()
            if new_description:
                theme.description = new_description.strip()
            logger.info(f"Theme {theme_id} renamed to '{new_title}'")
            return True

    @staticmethod
    def merge_themes(theme_id_source: str, theme_id_target: str, merged_title: Optional[str] = None) -> bool:
        """
        Merges theme_id_source into theme_id_target:
        - Re-maps all item mappings from source to target
        - Recalculates item counts and average severity for target
        - Deactivates or removes source theme
        """
        with get_db() as db:
            source = db.query(Theme).filter(Theme.id == theme_id_source).first()
            target = db.query(Theme).filter(Theme.id == theme_id_target).first()

            if not source or not target:
                logger.warning("Source or target theme not found.")
                return False

            # Update mappings
            mappings = db.query(ItemThemeMapping).filter(ItemThemeMapping.theme_id == theme_id_source).all()
            for m in mappings:
                m.theme_id = theme_id_target

            # Update target totals
            total_items = target.item_count + source.item_count
            if total_items > 0:
                target.avg_severity = (
                    (target.avg_severity * target.item_count + source.avg_severity * source.item_count) / total_items
                )
            target.item_count = total_items

            if merged_title:
                target.title = merged_title.strip()

            # Mark source inactive
            source.is_active = False
            source.item_count = 0

            logger.info(f"Merged theme {theme_id_source} into {theme_id_target}.")
            return True

    @staticmethod
    def toggle_theme_status(theme_id: str, is_active: bool) -> bool:
        """Enables or disables a theme from downstream opportunity matrix calculations."""
        with get_db() as db:
            theme = db.query(Theme).filter(Theme.id == theme_id).first()
            if not theme:
                return False
            theme.is_active = is_active
            return True


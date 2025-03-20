"""
UI components for the CAREScan ProForma Editor application.

This package contains modules for each tab in the Streamlit application,
separating the UI rendering logic from the core application logic.
"""

# These will be uncommented as each module is created
from ui.revenue_tab import render_revenue_tab
from ui.equipment_tab import render_equipment_tab
from ui.personnel_tab import render_personnel_tab
from ui.exams_tab import render_exams_tab
from ui.other_expenses_tab import render_other_expenses_tab
from ui.plots_tab import render_plots_tab
from ui.comprehensive_tab import render_comprehensive_tab

__all__ = [
    'render_revenue_tab',
    'render_equipment_tab',
    'render_personnel_tab',
    'render_exams_tab',
    'render_other_expenses_tab',
    'render_plots_tab',
    'render_comprehensive_tab',
] 
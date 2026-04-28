# Tooltip System Bug Fix & Architecture (V2.6.28)

## Issue Overview
Users reported that the `DUT` page tooltips (like the refresh button and com port dropdown) were completely invisible, even though other pages (like the Settings tab) displayed tooltips correctly. 

## Root Cause Analysis
This was a complex issue resulting from the interplay of global state management and differing API calls within the UI components.

1. **Global Toggle Bug (`ToolTip_Enabled`)**:
   - The user had previously disabled tooltips in the settings, which saved `"ToolTip_Enabled": false` inside their `setup.json`.
   - When the `DUT` page components initialize, they read this setting. `ToolTipManager.set_all_enabled(False)` is called, changing the manager's global state.
2. **API Divergence in `add_tooltip` vs `add_tooltip_with_text`**:
   - The `DUT` page uses `add_tooltip(widget, key)`. This method had an early return: `if not self.enabled: return`. Because of the early return, the tooltips were **never created or bound** to the DUT widgets.
   - The `SettingsTab` uses `add_tooltip_with_text(widget, text)`. This method **lacked** the early return. It created tooltips unconditionally, allowing Settings tooltips to show up despite the global "disabled" state.
3. **Recovery Impossibility**:
   - Since `add_tooltip` completely skipped creation when disabled, subsequently toggling "Enable Tooltips" in the Settings menu could not resurrect the DUT tooltips—there were no `ToolTip` objects in memory to re-enable.

## Solution Implemented
1. **Unconditional Creation, Conditional Display**:
   - Removed the `if not self.enabled` guard from `add_tooltip`.
   - Tooltips are now *always* instantiated and bound to their respective widgets during initialization.
   - Instead of skipping creation, the manager sets `tooltip.enabled = self.enabled`.
   - The display logic (`ToolTip.on_enter`) natively respects this `enabled` flag, silently returning if `False`.
2. **Preventing Duplicate Event Bindings**:
   - Modified `add_tooltip` to check if a tooltip already exists for a widget (`id(widget) in self.tooltips`).
   - If it exists, it updates the text, side, and state *in place* instead of recreating the `ToolTip` object. This prevents Tkinter's `bind(..., add=True)` from attaching multiple overlapping hover events, which causes instability.
3. **INI Load Failure Fix**:
   - Fixed a silent failure in `load_tooltip_config()` where `os.path.getcwd()` (invalid) was used instead of `os.getcwd()`. This ensures the fallback `tooltips.ini` merging logic executes correctly.

## Future Recommendations
When modifying or adding new tooltips:
- Always define new tooltip string keys in `tooltip.py -> _get_builtin_config()`.
- Ensure new tabs or components use the standard `ToolTipManager` instance instead of creating local ones to ensure the global enable/disable state is synchronized properly.

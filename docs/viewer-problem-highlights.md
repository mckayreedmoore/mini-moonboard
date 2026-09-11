# Problem highlights in the viewer

Open either Mini setup, expand **Problem**, and enable **Edit problem**. Choose Start, Hand, Foot, Finish, or Erase, then click a hold. Keyboard users can choose a grid position and press **Apply**. Turning editing off restores ordinary hold inspection without removing the marks.

Colored rings mark the chosen holds; the legend and position list also identify each role in text. These are manually entered problems, not imports from or endorsements by Moon Climbing. The viewer does not enforce climbing rules or grades.

**Copy link** shares the setup and marked positions through the URL. If clipboard access is unavailable, a selectable link appears. Reloading a valid link restores its marks with editing off. Switching between the 2020 and 2025 setups clears marks because the layouts differ. **Clear** removes the current problem; there is no separate saved-problem library.

Hiding holds or inspecting a connection temporarily disables the editor and hides its rings. The marks return with the holds. Approximate hold shapes and illustrative kicker orientations retain the limitations documented for each setup.

Browser regression coverage lives in `scripts/check_problem_highlights.cjs`; run it against a locally served `site/` with a Playwright module path as its first argument and the server URL as its second.

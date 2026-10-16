
import streamlit as st


# HTML structure
SLIDER_HTML = """
<div class="slider-container">
    <div class="value-bubble"></div>
    <input class="playlist-range" type="range" />
    <div class="marks"></div>
</div>
"""


# Visual styling
SLIDER_CSS = """
.slider-container {
    position: relative;
    padding: 26px 8px 10px;
    font-family: var(--st-font, Arial, sans-serif);
    color: var(--st-text-color, #fafafa);
}

.playlist-range {
    appearance: none;
    -webkit-appearance: none;
    display: block;
    width: 100%;
    height: 4px;
    margin: 0;
    border: none;
    border-radius: 4px;
    background: linear-gradient(
        to right,
        #ff4b4b 0%,
        #ff4b4b var(--progress),
        #555555 var(--progress),
        #555555 100%
    );
    cursor: pointer;
    outline: none;
}

.playlist-range::-webkit-slider-thumb {
    appearance: none;
    -webkit-appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #ff4b4b;
    border: none;
}

.playlist-range::-moz-range-thumb {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #ff4b4b;
    border: none;
}

.value-bubble {
    position: absolute;
    top: 0;
    left: 0;
    color: #ff4b4b;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
    pointer-events: none;
}

.marks {
    position: relative;
    height: 32px;
    margin-top: 5px;
}

.mark {
    position: absolute;
    transform: translateX(-50%);
    text-align: center;
    font-size: 11px;
    white-space: nowrap;
    color: #aaa;
}

.mark:first-child {
    transform: translateX(0);
}

.mark:last-child {
    transform: translateX(-100%);
}

.tick {
    display: block;
    width: 1px;
    height: 8px;
    background: #aaa;
    margin: 0 auto 5px;
}
"""


# Interactive behavior
SLIDER_JS = """
export default function({ parentElement, data, setStateValue }) {
    const container = parentElement.querySelector(".slider-container");
    const slider = parentElement.querySelector(".playlist-range");
    const output = parentElement.querySelector(".value-bubble");
    const marksContainer = parentElement.querySelector(".marks");

    const minimum = Number(data.minimum);
    const maximum = Number(data.maximum);

    slider.min = minimum;
    slider.max = maximum;
    slider.step = data.step;
    slider.setAttribute("aria-label", data.label);

    // Restore the selected value from Python
    const selected = Number(data.value);
    if (Number(slider.value) !== selected) {
        slider.value = selected;
    }

    function formatValue(value) {
        value = Number(value);

        if (data.mode === "songs") {
            return value + " Songs";
        }

        const hours = Math.floor(value / 60);
        const minutes = value % 60;

        if (!hours) return minutes + " min";
        if (!minutes) return hours + " hr";

        return hours + " hr " + minutes + " min";
    }

    // Generate persistent labeled tick marks
    marksContainer.replaceChildren();

    data.marks.forEach(mark => {
        const position =
            ((mark - minimum) / (maximum - minimum)) * 100;

        const element = document.createElement("span");
        element.className = "mark";
        element.style.left = position + "%";

        const tick = document.createElement("span");
        tick.className = "tick";

        const label = document.createElement("span");
        label.textContent =
            data.mode === "songs" ? mark : formatValue(mark);

        element.appendChild(tick);
        element.appendChild(label);
        marksContainer.appendChild(element);
    });

    function updateDisplay() {
        const value = Number(slider.value);

        const progress =
            ((value - minimum) / (maximum - minimum)) * 100;

        slider.style.setProperty("--progress", progress + "%");

        output.textContent = formatValue(value);

        // Align the bubble with the thumb, including at the edges
        const trackWidth = slider.getBoundingClientRect().width;
        const thumbRadius = 7;
        const thumbX =
            thumbRadius +
            (progress / 100) * (trackWidth - 2 * thumbRadius);

        output.style.left = (slider.offsetLeft + thumbX) + "px";

        if (progress <= 3) {
            output.style.transform = "translateX(0)";
        } else if (progress >= 95) {
            output.style.transform = "translateX(-100%)";
        } else {
            output.style.transform = "translateX(-50%)";
        }
    }

    // Update appearance immediately while dragging
    slider.oninput = updateDisplay;

    // Send the final selected value back to Python
    slider.onchange = () => {
        setStateValue("value", Number(slider.value));
    };

    updateDisplay();
}
"""


# Register the component once
_slider_component = st.components.v2.component(
    name="photo_playlist_slider",
    html=SLIDER_HTML,
    css=SLIDER_CSS,
    js=SLIDER_JS,
)


def playlist_slider(label, minimum, maximum, default, step, marks, mode, key):
    """Render a labeled slider and return its selected value."""

    # Read the previous selection, if one exists
    previous = st.session_state.get(key, {})

    if isinstance(previous, dict):
        value = previous.get("value", default)
    else:
        value = default
        del st.session_state[key]
        
    # Ensure the value remains inside the allowed range
    value = max(minimum, min(maximum, int(value)))

    result = _slider_component(
        key=key,
        data={
            "label": label,
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
            "marks": marks,
            "mode": mode,
            "value": value,
        },
        default={"value": value},
        on_value_change=lambda: None,
    )

    return int(result.value if result.value is not None else value)

import PropTypes from "prop-types";
import React from "react";

function FormInput({
  autocapitalize,
  autocomplete,
  autocorrect,
  className,
  hideLabel,
  hintText,
  id,
  inputClassName,
  inputmode,
  label,
  labelClass,
  onChange,
  placeholder,
  required,
  type,
  value,
}) {
  return (
    <div className={className}>
      <label
        className={`inline-block font-semibold text-lg text-slate-900 cursor-pointer ${labelClass} ${
          hideLabel ? "sr-only" : "null"
        }`}
        htmlFor={id}
      >
        {label}

        {required ? (
          <span aria-hidden="true" className="text-bn-ribbon-700 font-bold">
            *
          </span>
        ) : null}
      </label>

      {hintText ? (
        <p className="mb-2 text-sm text-gray-700">{{ hintText }}</p>
      ) : null}

      <div className="relative">
        <input
          autoCapitalize={autocapitalize}
          autoComplete={autocomplete}
          autoCorrect={autocorrect}
          className={`
            block w-full border-slate-300 text-slate-900 shadow-sm
            focus:border-oxford-500 focus:ring-oxford-500
            sm:text-sm
            [&:not(:placeholder-shown):not(:focus)]:invalid:border-bn-ribbon-600 [&:not(:placeholder-shown):not(:focus)]:invalid:ring-bn-ribbon-600 [&:not(:placeholder-shown):not(:focus)]:invalid:ring-1
            ${inputClassName}
            ${!hideLabel ? "mt-1" : ""}
          `}
          id={id}
          inputMode={inputmode}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          type={type}
          value={value}
        />

        {/* {% if field.errors %}
        <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
          {% icon_exclamation_circle_mini class="h-4 w-4 text-red-500" %}
        </div>
      {% endif %} */}
      </div>

      {/* {% if field.errors %}
      <ul class="mt-2 text-sm text-bn-ribbon-600">
        {% for error in field.errors %}
          <li>{{ error }}</li>
        {% endfor %}
      </ul>
    {% endif %} */}
    </div>
  );
}

export default FormInput;

FormInput.propTypes = {
  autocapitalize: PropTypes.string,
  autocomplete: PropTypes.oneOf([
    "none",
    "off",
    "characters",
    "words",
    "sentences",
  ]),
  autocorrect: PropTypes.oneOf(["on", "off"]),
  className: PropTypes.string,
  hideLabel: PropTypes.bool,
  hintText: PropTypes.string,
  id: PropTypes.string,
  inputClassName: PropTypes.string,
  inputmode: PropTypes.string,
  label: PropTypes.string,
  labelClass: PropTypes.string,
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  required: PropTypes.bool,
  type: PropTypes.string,
  value: PropTypes.string,
};

FormInput.defaultProps = {
  autocapitalize: null,
  autocomplete: null,
  autocorrect: null,
  className: null,
  hideLabel: false,
  hintText: null,
  id: "inputID",
  inputClassName: null,
  inputmode: null,
  label: null,
  labelClass: null,
  onChange: () => null,
  placeholder: null,
  required: null,
  type: "text",
  value: null,
};

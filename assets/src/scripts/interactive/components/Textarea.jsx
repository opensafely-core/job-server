import { Field, useFormikContext } from "formik";
import { bool, node, number, string } from "prop-types";
import React, { useEffect, useState } from "react";
import CharCount from "./CharCount";
import HintText from "./HintText";

function Textarea({
  characterCount,
  children,
  className,
  hintText,
  id,
  label,
  maxlength,
  minlength,
  placeholder,
  name,
  resize,
  rows,
  required,
}) {
  const { setFieldValue, values } = useFormikContext();
  const [textVal, setTextVal] = useState(values[id] || "");

  useEffect(() => {
    setFieldValue(id, textVal);
  }, [textVal, id, setFieldValue]);

  return (
    <div className={`flex flex-col gap-y-3 text-lg leading-tight ${className}`}>
      <label className="font-semibold tracking-tight" htmlFor={id}>
        {label}
      </label>
      {hintText ? <HintText>{hintText}</HintText> : null}
      <Field
        as="textarea"
        className={`
          mt-1 block w-full max-w-prose rounded-md border-gray-400 text-gray-900 shadow-sm
          ${resize ? "" : "resize-none"}
          sm:text-sm
          focus:outline-none focus:ring-oxford-500 focus:border-oxford-500
        `}
        maxLength={maxlength}
        minLength={minlength}
        name={name}
        onChange={(e) => setTextVal(e.target.value)}
        placeholder={placeholder}
        required={required}
        rows={rows}
        value={textVal}
      />
      {characterCount && (minlength || maxlength) ? (
        <CharCount current={textVal.length} max={maxlength} min={minlength} />
      ) : null}
      {children}
    </div>
  );
}

export default Textarea;

Textarea.defaultProps = {
  className: null,
  children: null,
  characterCount: false,
  hintText: null,
  maxlength: null,
  minlength: null,
  placeholder: null,
  required: false,
  rows: 8,
};

Textarea.propTypes = {
  characterCount: bool,
  children: node,
  className: string,
  hintText: node,
  id: string.isRequired,
  label: string.isRequired,
  maxlength: number,
  minlength: number,
  name: string.isRequired,
  placeholder: string,
  required: bool,
  resize: bool.isRequired,
  rows: number,
};

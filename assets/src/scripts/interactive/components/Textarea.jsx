import { Field, useFormikContext } from "formik";
import { bool, node, number, string } from "prop-types";
import React, { useEffect } from "react";
import CharCount from "./CharCount";
import HintText from "./HintText";

function Textarea({
  characterCount = false,
  children = null,
  className = null,
  hintText = null,
  id,
  label,
  maxlength = null,
  minlength = null,
  name,
  placeholder = null,
  required = false,
  resize,
  rows = 8,
  value = "",
}) {
  const { setFieldValue, values } = useFormikContext();

  useEffect(() => {
    setFieldValue(id, values[id] || value);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
        placeholder={placeholder}
        required={required}
        rows={rows}
      />
      {characterCount && (minlength || maxlength) ? (
        <CharCount field={id} max={maxlength} min={minlength} />
      ) : null}
      {children}
    </div>
  );
}

export default Textarea;

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
  value: string,
};

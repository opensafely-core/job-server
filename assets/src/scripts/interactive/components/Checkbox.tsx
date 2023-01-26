import { Field } from "formik";
import React from "react";

interface CheckboxProps {
  id: string;
  label: string;
  name: string;
  onClick?: React.MouseEventHandler<HTMLInputElement>;
  value: string;
}

function Checkbox({ id, label, name, value, onClick }: CheckboxProps) {
  return (
    <div className="flex flex-row place-items-baseline gap-x-3 text-lg leading-tight">
      <Field
        className="peer cursor-pointer scale-150 top-[1px] relative checked:bg-oxford-600 focus:ring-bn-sun"
        id={id}
        name={name}
        onClick={onClick}
        type="checkbox"
        value={value}
      />
      <label
        className="cursor-pointer touch-manipulation tracking-tight"
        htmlFor={id}
      >
        {label}
      </label>
    </div>
  );
}

export default Checkbox;

Checkbox.defaultProps = {
  onClick: () => null,
};

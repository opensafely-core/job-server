import { Field } from "formik";
import { func, string } from "prop-types";

function RadioButton({ id, label, name, value, onClick }) {
  return (
    <div className="flex flex-row place-items-baseline gap-x-3 text-lg leading-tight">
      <Field
        className="peer cursor-pointer scale-150 top-[1px] relative checked:bg-oxford-600 focus:ring-bn-sun"
        id={id}
        name={name}
        onClick={onClick}
        type="radio"
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

export default RadioButton;

RadioButton.propTypes = {
  id: string.isRequired,
  label: string.isRequired,
  name: string.isRequired,
  onClick: func,
  value: string.isRequired,
};

RadioButton.defaultProps = {
  onClick: () => null,
};

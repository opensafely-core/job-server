import { Field } from "formik";
import { string } from "prop-types";
import React from "react";

function Textarea({ name }) {
  return (
    <div className="flex flex-row place-items-baseline gap-x-3 text-lg leading-tight">
      <Field
        as="textarea"
        classname="
          mt-1 block w-full rounded-md border-slate-300 text-slate-900 shadow-sm
          {% if not resize %}resize-none{% endif %}
          sm:text-sm
          focus:border-oxford-500 focus:ring-oxford-500
          invalid:border-bn-ribbon-600 invalid:ring-bn-ribbon-600 invalid:ring-1
        "
        name={name}
      />
    </div>
  );
}

export default Textarea;

Textarea.propTypes = {
  name: string.isRequired,
};

import { useFormikContext } from "formik";
import { number, string } from "prop-types";
import React from "react";

function CharCount({ field, min = null, max = null }) {
  const { values } = useFormikContext();
  const current = values?.[field].length;

  if (current === max) {
    return <p className="text-sm">No characters remaining</p>;
  }

  if (current < min) {
    return <p className="text-sm">{current - min} more characters required</p>;
  }

  if (current < max) {
    return <p className="text-sm">{max - current} characters remaining</p>;
  }

  if (current > max) {
    return <p className="text-sm">Remove {current - max} characters</p>;
  }

  return <p className="text-sm"> chars remaining</p>;
}

CharCount.propTypes = {
  field: string.isRequired,
  min: number,
  max: number,
};

export default CharCount;

import React from "react";
import useFile from "../../hooks/use-file";
import useStore from "../../stores/use-store";
import classes from "./Text.module.scss";

function Text() {
  const { file } = useStore();
  const { data } = useFile(file);
  return <pre className={classes.txt}>{data}</pre>;
}

export default Text;

use pyo3::prelude::*;

#[pymodule]
fn holdem_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    Ok(())
}

#[pyfunction]
fn hello() -> &'static str {
    holdem_core::hello()
}
import nox


@nox.session(python=["3.11", "3.12", "3.13", "3.14", "3.15"])
def tests(session):
    session.install(".[test]")
    session.run("pytest", "-W", "error")

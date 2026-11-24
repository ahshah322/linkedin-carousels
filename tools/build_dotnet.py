"""Build .NET carousel PDFs from template/ using per-topic specs.
Usage: python3 tools/build_dotnet.py [slug ...]   (no args = all)
Writes dotnet/<slug>.pdf (work files go to build-dotnet/<slug>/, git-ignored).
"""
import html, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = lambda n: open(f"{ROOT}/template/{n}.dc.html").read()
E = html.escape

KW = {"public", "private", "class", "interface", "abstract", "override", "static", "readonly", "const", "void",
      "int", "string", "decimal", "double", "var", "new", "async", "await", "get", "set", "return", "bool", "using"}
PURPLE, NAME, STR, COM = "#A894FF", "#E4DEFF", "#FFC8A6", "#B9B5D2"


def hl(line):
    if not line.strip():
        return '<div style="white-space:pre">&nbsp;</div>\n'
    out, prev = [], None
    for tok in re.findall(r'//.*|"[^"]*"|\w+|\s+|.', line):
        if tok.startswith("//"):
            out.append(f'<span style="color:{COM}">{E(tok)}</span>')
        elif tok.startswith('"'):
            out.append(f'<span style="color:{STR}">{E(tok)}</span>')
        elif tok in KW:
            out.append(f'<span style="color:{PURPLE}">{E(tok)}</span>')
        elif prev in ("class", "interface") and re.match(r"\w+", tok):
            out.append(f'<span style="color:{NAME}">{E(tok)}</span>')
        else:
            out.append(E(tok))
        if tok.strip():
            prev = tok
    return f'<div style="white-space:pre">{"".join(out)}</div>\n'


def size(text, base, avail, k=0.6):
    return min(base, int(avail / (len(text) * k)))


def code_block(h, code):
    return re.sub(r'(?:<div style="white-space:pre">.*?</div>\n)+',
                  lambda m: "".join(hl(l) for l in code.split("\n")), h, count=1, flags=re.S)


def seq(h, pattern, vals, flags=re.S):
    it = iter(vals)
    return re.sub(pattern, lambda m: m.group(1) + E(next(it)) + m.group(m.lastindex), h, flags=flags)


def concept(h, c):
    h = re.sub(r"font:800 104px/1\.05", f"font:800 {size(c['h1'], 104, 690, 0.56)}px/1.05", h)
    h = re.sub(r"(<h1[^>]*>)[^<]*(</h1>)", lambda m: m.group(1) + E(c["h1"]) + m.group(2), h, count=1)
    h = re.sub(r'(letter-spacing:0\.08em;padding:14px 28px;border-radius:999px;">)[^<]*(</span>)',
               lambda m: m.group(1) + E(c["pill"]) + m.group(2), h, count=1)
    h = re.sub(r'(<p style="margin:10px 0 0 0;[^>]*>)[^<]*(</p>)', lambda m: m.group(1) + E(c["sub"]) + m.group(2), h, count=1)
    h = code_block(h, c["code"])
    h = seq(h, r'(color:#EDE8FF">)(.*?)(</span></div>)', c["how"])
    h = re.sub(r"(USE IT FOR</span>\n<span[^>]*>)[^<]*(</span>)", lambda m: m.group(1) + E(c["use"]) + m.group(2), h)
    h = re.sub(r"(WATCH OUT</span></span>\n<span[^>]*>)[^<]*(</span>)", lambda m: m.group(1) + E(c["watch"]) + m.group(2), h)
    return h


def cover(h, s):
    a, b = s["words"]
    h = seq(h, r"(font:800 172px/1\.0 'Nunito',sans-serif;[^>]*>)(.*?)(</span>)", [a, b])
    sizes = iter([size(a, 172, 900), size(b, 172, 900)])
    h = re.sub(r"font:800 172px/1\.0", lambda m: f"font:800 {next(sizes)}px/1.0", h)
    h = re.sub(r'(<p style="margin:34px 0 0 0;[^>]*>)[^<]*(</p>)', lambda m: m.group(1) + E(s["tag"]) + m.group(2), h, count=1)
    h = seq(h, r"(font:500 32px/1\.2 'Nunito',sans-serif;color:#fff\">)(.*?)(</span>)", s["agenda"])
    return h


def compare(h, s):
    a, b = s["words"]
    pills = iter(s["pills"])
    h = re.sub(r'(letter-spacing:0\.08em;padding:14px 28px;border-radius:999px;">)[^<]*(</span>)',
               lambda m: m.group(1) + E(next(pills)) + m.group(2), h)
    rows = iter(s["rows"])

    def row(m):
        l, x, y = next(rows)
        return m.group(1) + E(l) + m.group(3) + E(x) + m.group(5) + E(y) + m.group(7)

    h = re.sub(r"(padding:18px 0\">)(.*?)(</div><div[^>]*#8B6CFF[^>]*\">)(.*?)(</div><div[^>]*#C9BCFF[^>]*\">)(.*?)(</div>)", row, h, flags=re.S)
    h = re.sub(r"(RULE OF THUMB</span>\n<span[^>]*>)[^<]*(</span>)", lambda m: m.group(1) + E(s["rule"]) + m.group(2), h)
    return h


def cta(h, s):
    a, b = s["words"]
    h = re.sub(r'Class or (<span style="[^"]*">)Struct(</span>\?)',
               lambda m: f'{E(s["cta_a"])} or {m.group(1)}{E(s["cta_b"])}{m.group(2)}', h)
    h = re.sub(r'(<p style="margin:16px 0 0 0;[^>]*>)[^<]*(</p>)', lambda m: m.group(1) + E(s["cta_sub"]) + m.group(2), h, count=1)
    return h


AGENDA = ["{0}", "Real C# code for both", "When to pick which in real projects", "The pitfall to watch for",
          "A side-by-side comparison table"]


def spec(**k):
    return k


SPECS = {}

SPECS["class-vs-interface"] = spec(
    words=("Class", "Interface"), tag="One gives you code. The other a promise.",
    agenda=[x.format("What each one defines") for x in AGENDA], pills=("CLASS", "INTERFACE"),
    a=dict(h1="Class", pill="CLASS", sub="Blueprint · state and implementation",
           code='public class EmailSender\n{\n    public string Host { get; set; } = "smtp";\n    public void Send(string to) { }\n}\n\nvar sender = new EmailSender();\nsender.Send("ali@dev.com");',
           how=["Holds state and real implementation", "Created with new", "Inherits from only one base class"],
           use="Concrete types that do the work, like services and entities.",
           watch="Depending on one directly makes it hard to swap or mock."),
    b=dict(h1="Interface", pill="INTERFACE", sub="Contract · what a type must offer",
           code='public interface IEmailSender\n{\n    void Send(string to);\n}\n\npublic class SmtpSender : IEmailSender\n{\n    public void Send(string to) { }\n}',
           how=["Lists members, holds no instance state", "Cannot be created with new", "A type can implement many"],
           use="Loose coupling, dependency injection and easy mocking.",
           watch="Do not add one per class by default. Wait for a real need."),
    rows=[("Purpose", "Defines how it works", "Defines what it offers"), ("State", "Fields and state", "No instance fields"),
          ("Create", "Yes, with new", "No, not directly"), ("Inherit", "One base class", "Many interfaces"),
          ("Members", "Fully implemented", "Signatures (defaults C# 8+)"), ("Testing", "Harder to mock", "Easy to mock"),
          ("Best for", "Concrete behavior", "Contracts and DI")],
    rule="Build with classes. Depend on interfaces so you can swap and test.",
    cta_a="Class", cta_b="Interface", cta_sub="Do you design around interfaces first? Tell me in the comments.")

SPECS["abstract-class-vs-interface"] = spec(
    words=("Abstract Class", "Interface"), tag="Shared code or shared capability?",
    agenda=[x.format("What each one is for") for x in AGENDA], pills=("ABSTRACT", "INTERFACE"),
    a=dict(h1="Abstract Class", pill="ABSTRACT", sub="Shared base · code for related types",
           code='public abstract class Shape\n{\n    public string Name { get; set; } = "";\n    public abstract double Area();\n    public void Log() => Console.WriteLine(Name);\n}\n\nvar s = new Shape();  // compile error',
           how=["Holds fields, constructors and logic", "Mixes abstract and ready members", "A type can inherit only one"],
           use="Closely related types that share state or common logic.",
           watch="Cannot be created with new, and it uses up your one base class."),
    b=dict(h1="Interface", pill="INTERFACE", sub="Shared capability · works across any types",
           code='public interface IPrintable\n{\n    void Print();\n}\n\npublic class Invoice : IPrintable\n{\n    public void Print() { }\n}',
           how=["Describes what a type can do", "No fields or constructors", "Many per type, even unrelated"],
           use="A capability unrelated types share, like IDisposable or IComparable.",
           watch="No shared state to reuse across implementers."),
    rows=[("Fields", "Yes", "No instance fields"), ("Constructor", "Yes", "No"),
          ("Code", "Implemented and abstract", "Signatures (defaults C# 8+)"), ("Inherit", "Only one", "Many"),
          ("Relation", "Related types", "Any types"), ("Create", "No, not directly", "No, not directly"),
          ("Best for", "Shared base logic", "Shared capability")],
    rule="Related types sharing logic? Abstract class. Same ability across unrelated types? Interface.",
    cta_a="Abstract Class", cta_b="Interface", cta_sub="Which one do you reach for first? Tell me in the comments.")

SPECS["field-vs-property"] = spec(
    words=("Field", "Property"), tag="Looks the same. Protects very differently.",
    agenda=[x.format("How each one stores data") for x in AGENDA], pills=("FIELD", "PROPERTY"),
    a=dict(h1="Field", pill="FIELD", sub="Raw storage · direct access",
           code='public class Account\n{\n    public decimal Balance;  // field\n}\n\nvar a = new Account();\na.Balance = -500;  // no validation',
           how=["A variable declared in a class", "Direct access, no logic", "Cannot live in an interface"],
           use="Private backing storage, like private readonly fields.",
           watch="A public field lets anyone set any value. System.Text.Json skips it by default."),
    b=dict(h1="Property", pill="PROPERTY", sub="Controlled access · get and set",
           code='public class Account\n{\n    private decimal _balance;\n    public decimal Balance\n    {\n        get => _balance;\n        set => _balance = Math.Max(0, value);\n    }\n}',
           how=["Get and set accessors wrap the data", "Can validate, compute or be read-only", "Works in interfaces and data binding"],
           use="Anything public: models, DTOs, settings. { get; set; } is the default.",
           watch="A property can hide slow logic. Keep getters cheap."),
    rows=[("Stores", "Data directly", "Via get and set"), ("Validate", "Not possible", "Built into set"),
          ("Read-only", "readonly keyword", "Omit set, or use init"), ("Interface", "Not allowed", "Allowed"),
          ("Binding", "Not supported", "Supported"), ("Serialize", "Skipped by default", "Supported"),
          ("Best for", "Private backing data", "Public API")],
    rule="Keep fields private. Expose data through properties.",
    cta_a="Field", cta_b="Property", cta_sub="Do you ever use a public field on purpose? Tell me in the comments.")

SPECS["property-vs-method"] = spec(
    words=("Property", "Method"), tag="Same dot. Different promise.",
    agenda=[x.format("What each one promises") for x in AGENDA], pills=("PROPERTY", "METHOD"),
    a=dict(h1="Property", pill="PROPERTY", sub="Looks like data · no parentheses",
           code='public class Order\n{\n    public decimal Subtotal { get; set; }\n    public decimal Tax { get; set; }\n    public decimal Total => Subtotal + Tax;\n}\n\nConsole.WriteLine(order.Total);',
           how=["Read like a field, no parentheses", "No parameters (indexers aside)", "Cheap and free of side effects"],
           use="Simple values and cheap calculations, like order.Total.",
           watch="A slow or throwing getter surprises every caller."),
    b=dict(h1="Method", pill="METHOD", sub="Does work · parentheses and parameters",
           code='public class Order\n{\n    public decimal Subtotal { get; set; }\n    public decimal Tax { get; set; }\n    public decimal CalculateTotal(decimal off)\n    {\n        return Subtotal + Tax - off;\n    }\n}',
           how=["Takes parameters", "Can do heavy work or change state", "Can throw or run async"],
           use="Actions and work with side effects: Save, Send, Calculate.",
           watch="If it reads like a verb, make it a method."),
    rows=[("Syntax", "No parentheses", "Parentheses"), ("Input", "None", "Any parameters"),
          ("Cost", "Cheap to read", "Can be heavy"), ("Effects", "Avoid them", "Allowed"),
          ("Async", "Not practical", "Yes, with Task"), ("Naming", "A noun", "A verb"),
          ("Best for", "Data-like values", "Actions and work")],
    rule="Noun for data, verb for work. If it could surprise the caller, make it a method.",
    cta_a="Property", cta_b="Method", cta_sub="What is your rule for choosing? Tell me in the comments.")

SPECS["const-vs-readonly"] = spec(
    words=("const", "readonly"), tag="Both stay fixed. When is the question.",
    agenda=[x.format("When each value is fixed") for x in AGENDA], pills=("CONST", "READONLY"),
    a=dict(h1="const", pill="CONST", sub="Compile-time · baked into callers",
           code='public class Limits\n{\n    public const int MaxRetries = 3;\n    public const string Name = "Api";\n}\n\nvar n = Limits.MaxRetries;  // inlined',
           how=["Value fixed at compile time", "Primitives, strings, enums, null", "Implicitly static"],
           use="True constants that never change, like Pi or days in a week.",
           watch="A public const is baked into callers. Change it and they must recompile."),
    b=dict(h1="readonly", pill="READONLY", sub="Runtime · set once, then fixed",
           code='public class Client\n{\n    public readonly string Id;\n    public readonly List<int> Tags = new();\n    public Client(string id) => Id = id;\n}\n\n// Tags.Add(1) still works',
           how=["Set at declaration or in the constructor", "Works with any type", "Can differ per instance"],
           use="Values known at startup or created per instance.",
           watch="It blocks reassigning, not mutating. Tags.Add still works."),
    rows=[("Set when", "Compile time", "Runtime"), ("Types", "Primitives, string, enum", "Any type"),
          ("Static", "Always", "Optional"), ("Instance", "Same for all", "Can differ"),
          ("Compiled", "Inlined into callers", "Normal field read"), ("Library", "Callers recompile", "Callers unaffected"),
          ("Best for", "True constants", "Startup values")],
    rule="const for values that never change. readonly for everything else.",
    cta_a="const", cta_b="readonly", cta_sub="Ever been bitten by a const that should be readonly? Tell me.")


def build(slug):
    s = SPECS[slug]
    d = f"{ROOT}/build-dotnet/{slug}"
    os.makedirs(d, exist_ok=True)
    pages = {"1-cover": cover(T("1-cover"), s), "2-concept-a": concept(T("2-concept-a"), s["a"]),
             "3-concept-b": concept(T("3-concept-b"), s["b"]), "4-compare": compare(T("4-compare"), s),
             "5-cta": cta(T("5-cta"), s)}
    for n, h in pages.items():
        open(f"{d}/{n}.dc.html", "w").write(h)
    out = f"{d}/{slug}.pdf"
    subprocess.run([sys.executable, f"{ROOT}/tools/render.py", d, out], check=True)
    os.makedirs(f"{ROOT}/dotnet", exist_ok=True)
    os.replace(out, f"{ROOT}/dotnet/{slug}.pdf")


if __name__ == "__main__":
    for slug in (sys.argv[1:] or SPECS):
        build(slug)

OrthOpen is an open source add-on in blender to facilitate design of orthopaedic aids. This pages is aimed towards developers. 
A guide aimed at end users of this plugin is coming soon.

## Getting started 
It is recommended to use an external IDE for edititing the source code. A suitable editor is 
Visual Studio Code with the [Blender Development extension](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)

### Other material
Guides that might be useful when getting started developing a Blender add-on.
[Create Simple Blender Addon in 15 Minutes](https://www.youtube.com/watch?v=Y67eCfiqJQU)
[Setup vscode for blender](https://www.youtube.com/watch?v=bmpKAluHiEc)

### Tips 
- Activate Python Tooltips from *User Preferences > Interface*

## Naming conventions 
We use the conventions proposed by Blender: [Blender 2.80: Addon API](https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Addons) and 
PEP8. The Blender conventions partly conflict those of PEP8. In case of a conflict the precedence order is 

1. Blender conventions
2. PEP8

where a lower number indicates higher precedence.

## Git conventions 
- Work in feature branches. When a feature branch is tested this feature is merged to *master*. The latest commit of branch *master* should always be code that can be released. So, only put finished features there.
- Use explicit merge commit in *master*, even if a fast-forward would have been possible. This is because that makes history more traceable.
-[Commit message guide lines](https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines)

## Design philosophy
The user of this plugin is assumed to be a novice at Blender. The goal is that the user only should have to be able to 
navigate the viewport and locate the add-on functions. Everything else should be possible to do using high level functions
provided by the add-on.

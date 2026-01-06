# Prompt pro OpenAI Codex - Oprava GH007 Git Email Error

Při push na GitHub dostávám chybu GH007: "push odmítnut kvůli ochraně soukromí emailu".

Mám zapnutou ochranu "Keep my email address private" na GitHubu, takže potřebuji použít GitHub noreply email místo skutečného emailu.

Pomoz mi prosím:

1. Najít můj GitHub noreply email (je v GitHub Settings → Emails, formát: USERNAME@users.noreply.github.com nebo ID+USERNAME@users.noreply.github.com)

2. Nastavit git, aby používal tento noreply email JEN pro toto repo (ne globálně):
   - Nastavit user.email na noreply adresu jen pro toto repo
   - Zachovat aktuální user.name

3. Opravit poslední commit, aby používal noreply email:
   - Amend posledního commitu s novým emailem
   - Zachovat commit message a změny

4. Pushnut opravený commit na origin/main

Ukaž mi přesné bash příkazy, předpokládej:
- Můj GitHub noreply email je: XXXXXXXX+milhy777@users.noreply.github.com (XXXXXXXX nahradím svým ID)
- Jsem v root adresáři repozitáře
- Branch je "main"
- Chci zachovat existující commit message

Důležité: Použij git config --local (ne --global), aby to ovlivnilo jen aktuální repozitář.

---

## Očekávané řešení

Codex by měl vygenerovat příkazy typu:

```bash
# 1. Najdi noreply email na: https://github.com/settings/emails

# 2. Nastav email jen pro toto repo
git config --local user.email "XXXXXXXX+milhy777@users.noreply.github.com"

# 3. Oprav poslední commit
git commit --amend --reset-author --no-edit

# 4. Push
git push origin main
```

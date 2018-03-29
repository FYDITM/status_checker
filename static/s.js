var TRK = TRK || {};
TRK.gameplay = function(game) {};

var readCookie = function(k) { return (document.cookie.match('(^|; )' + k + '=([^;]*)') || 0)[2]; };

var totalScore = 0;

var top5 = null;

TRK.gameplay.prototype = {
    init: function() {
        this.game.input.maxPointers = 1;
        this.game.stage.disableVisibilityChange = true;

        this.elapsed = 0;
        this.counter = 0;
        this.speed = 200;

        this.jumpForce = 0;
        this.maxJumpForce = 1500;
        this.slow = false;
        this.dash = false;
        this.dashSpeed = 300;
        totalScore = 0;
    },

    preload: function() {
        this.load.image('background', '/static/assets/images/background.png');
        this.load.image('soil_ground', '/static/assets/images/soil_ground.png'); //800x14
        this.load.spritesheet('racer', '/static/assets/images/racer.png', 128, 95, 6);
        this.load.spritesheet('hpbar', '/static/assets/images/hpbar.png', 153, 26, 2);
        this.load.spritesheet('ponczuchy', 'static/assets/images/ponczuchy.png', 40, 40);
        this.load.spritesheet('heart', '/static/assets/images/heart.png', 40, 36);

        this.load.audio('uuu', '/static/assets/sounds/uuu.mp3');
        this.load.audio('uu', '/static/assets/sounds/uu.mp3');
        this.load.audio('u', '/static/assets/sounds/u.mp3');
        this.load.audio('hurt', '/static/assets/sounds/hurt.wav');
        this.load.audio('heal', 'static/assets/sounds/heal.wav');
        this.load.audio('pon', '/static/assets/sounds/ponczuchy.mp3');

    },

    create: function() {
        this.background = this.add.tileSprite(0, 0, 1600, 640, 'background');
        this.player = this.add.sprite(0, 590, 'racer');
        this.player.health = this.player.maxHealth = 100;
        this.player.animations.add("ride", [0, 1, 2, 3], 4, true, true);
        this.player.animations.add("jump", [4], 4, false, true);
        this.player.animations.add("fall", [5], 4, false, true);

        this.hpbars = this.add.group();
        this.hpbarEmpty = this.add.sprite(this.game.width - 170, 10, "hpbar", 1);
        this.hpbarFull = this.add.sprite(this.hpbarEmpty.x, this.hpbarEmpty.y, "hpbar", 0);
        this.hpRect = new Phaser.Rectangle(0, 0, this.hpbarEmpty.width, this.hpbarEmpty.height);

        this.u = this.add.audio('u');
        this.uu = this.add.audio('uu');
        this.uuu = this.add.audio('uuu');
        this.hurt = this.add.audio('hurt');
        this.heal = this.add.audio('heal');
        this.pon = this.add.audio('pon');
        //this.sound.setDecodedCallback([this.uu, this.uuu], this.ready, this);

        this.physics.startSystem(Phaser.Physics.ARCADE);

        this.heart = this.add.sprite(0, 0, 'heart');
        this.heart.animations.add('idle', [...Array(14).keys()], 10, true, true);
        this.heart.kill();
        this.physics.enable(this.heart);
        this.ponczuchy = this.add.sprite(0, 0, 'ponczuchy');
        this.ponczuchy.animations.add('idle',[...Array(12).keys()], 10, true, true);
        this.ponczuchy.kill();
        this.physics.enable(this.ponczuchy);


        this.physics.enable(this.player);
        this.player.body.gravity.y = 1400;
        this.player.body.collideWorldBounds = true;
        this.player.anchor.set(0.5, 1);
        this.platforms = this.add.group();
        this.platforms.enableBody = true;
        this.ground = this.add.tileSprite(0, 590, 1600, 14, 'soil_ground');
        this.physics.enable(this.ground);
        this.ground.body.immovable = true;

        cursors = this.input.keyboard.createCursorKeys();
        this.scoreText = this.add.text(10, 20, totalScore);
        new Platform(this);
    },


    update: function() {
        this.scoreText.destroy();
        this.scoreText = this.add.text(10, 20, `punkty:\n  ${Math.trunc(totalScore)}`, { fontSize: 16 });

        this.physics.arcade.collide(this.player, this.ground);
        this.physics.arcade.collide(this.player, this.platforms, this.collide, null, this);
        this.physics.arcade.collide(this.player, this.heart, this.getHeart, null, this);
        this.physics.arcade.collide(this.player, this.ponczuchy, this.getPonczuchy, null, this);

        if (!this.heart.exists && this.rnd.frac() < 0.001) {
            this.placeHeart();
        }
        if (!this.ponczuchy.exists && this.rnd.frac() < 0.1) {
            this.placePonczuchy();
        }

        this.move();
        if (cursors.right.isDown) {
            this.dash = true;
        } else if (this.dash) {
            this.dash = false;
        }

        if (cursors.left.isDown) {
            this.slow = true;
        } else if (this.slow) {
            this.slow = false;
        }

        if ((cursors.up.isDown || this.input.keyboard.isDown(Phaser.KeyCode.SPACEBAR)) && this.player.body.touching.down) {
            this.jumpForce += this.jumpForce > this.maxJumpForce ? 0 : 30;
        } else if (this.player.body.touching.down && this.jumpForce > 0) {
            this.jump();
        }
        if (this.player.body.velocity.y < -50 && !this.player.body.touching.down) {
            this.player.animations.play('jump');
        } else if (this.player.body.velocity.y > 0 && !this.player.body.touching.down) {
            this.player.animations.play('fall');
        }

    },

    jump: function() {
        this.player.body.velocity.y = -this.jumpForce;
        if (this.jumpForce > this.maxJumpForce * 0.7) {
            this.uuu.play();
        } else if (this.jumpForce > this.maxJumpForce * 0.4) {
            this.uu.play();
        } else {
            this.u.play();
        }
        this.jumpForce = 0;
    },

    move: function() {
        let currSpeed = this.currentSpeed();
        this.player.animations.play('ride', currSpeed / 50, false);
        this.background.autoScroll(-currSpeed / 2, 0);
        this.ground.autoScroll(-currSpeed, 0);

        this.platforms.forEach(function(x) {
            if (x.x + x.width < 0) {
                x.destroy();
            } else {
                x.body.velocity.x = -currSpeed;
            }
        });

        if (this.heart.exists) {
            if (this.heart.right < 0) {
                this.heart.kill();
            } else {
                this.heart.body.velocity.x = -currSpeed;
            }
        }
        if (this.ponczuchy.exists) {
            if (this.ponczuchy.right < 0) {
                this.ponczuchy.kill();
            } else {
                this.ponczuchy.body.velocity.x = -currSpeed;
            }
        }

        let step = currSpeed / 1000;
        this.speed += step / 3;
        this.elapsed += step;
        totalScore += step;
        this.counter += step * 5;

        if (this.counter >= 100 && this.rnd.frac() < 0.4) {
            new Platform(this);
            this.counter = 0;
        }
    },

    collide: function() {
        this.onFloor();
        if (this.player.right < 0) {
            this.player.health = -1;
        }
        if (!this.player.body.touching.down || this.onFloor()) {
            this.damagePlayer();
        }
    },

    getHeart: function() {
        this.heart.kill();
        this.player.health = this.player.maxHealth;
        this.hpRect.width = Math.floor((this.player.health / this.player.maxHealth) * this.hpbarEmpty.width);
        this.hpbarFull.crop(this.hpRect);
        this.heal.play();
    },

    getPonczuchy: function() {
        this.ponczuchy.kill();
        totalScore += 200;
        this.pon.play();
    },

    stop: function() {
        this.background.stopScroll();
        this.ground.stopScroll();
        this.player.animations.play('ride');
        this.player.animations.stop('ride');
    },

    onFloor: function() {
        return this.player.bottom == 590;
    },

    damagePlayer: function() {
        this.player.damage(5);
        this.hpRect.width = Math.floor((this.player.health / this.player.maxHealth) * this.hpbarEmpty.width);
        this.hpbarFull.crop(this.hpRect);
        this.hurt.play("", 0, 1, false, false);

        if (this.player.health <= 0) {
            var game = this;
            req("/highscores", function(response) {
                top5 = JSON.parse(response);
                game.state.start("gameover");
            });

        }
    },

    placeHeart: function() {
        let x = this.world.bounds.width + 100;
        let y = this.rnd.integerInRange(100, this.world.height - 10);
        if (this.checkFreeSpace(new Phaser.Rectangle(x, y, this.heart.width, this.heart.height))) {
            this.heart.reset(x, y);
            this.heart.animations.play('idle');
        }
    },

    placePonczuchy: function() {
        let x = this.world.bounds.width+5;
        let y = this.rnd.integerInRange(100, this.world.height - 10);
        if (this.checkFreeSpace(new Phaser.Rectangle(x, y, this.ponczuchy.width, this.ponczuchy.height))) {
            this.ponczuchy.reset(x, y);
            this.ponczuchy.animations.play('idle');
        }
    },

    currentSpeed: function() {
        let c = this.dash ? 2 : (this.slow ? 0.5 : 1);
        return this.speed * c;
    },

    checkFreeSpace: function(rect) {
        let result = true;
        this.platforms.forEach(function(el) {
            if (Phaser.Rectangle.intersects(rect, el)) {
                result = false;
            }
        });
        return result;
    }
};



var Platform = function(game) {
    this.maxWidth = 400;
    this.maxHeight = 100;
    this.minWidth = 100;
    this.minHeight = 30;
    let width = game.rnd.integerInRange(this.minWidth, this.maxWidth);
    let height = game.rnd.integerInRange(this.minHeight, this.maxHeight);
    let x = game.world.bounds.width + 100;
    let y = game.rnd.integerInRange(game.world.height / 2, game.world.height - 50);
    if (!game.checkFreeSpace(new Phaser.Rectangle(x, y, width, height))) {

        return;
    }
    this.sprite = game.add.sprite(x, y, "soil_ground");
    this.sprite.width = width;
    this.sprite.height = height;
    game.physics.enable(this.sprite, Phaser.Physics.ARCADE);
    game.platforms.add(this.sprite);
    this.sprite.body.immovable = true;
};

var sk = "mmm";


TRK.gameover = function(game) {};

TRK.gameover.prototype = {
    preload: function() {
        totalScore = Math.trunc(totalScore);
        //top5 = [{ name: "Terlecki", score: 1500 }, { name: "JESTEM NAJLEPSZY", score: 1000 }, { name: "Terlecki", score: 950 }, { name: "Terlecki", score: 600 }, { name: "Terlecki", score: 500 }]

        this.topScore = totalScore > top5[4].score;
        if (this.topScore) {
            this.load.audio('gameOver', '/static/assets/sounds/jamamszczescie.mp3');
            this.load.image('submit', '/static/assets/images/submit.png');
        } else if (totalScore > 5000) {
            this.load.audio('gameOver', '/static/assets/sounds/milozaskoczony.mp3');
        } else if (totalScore > 1000) {
            this.load.audio('gameOver', '/static/assets/sounds/notrudnono.mp3');
        } else {
            this.load.audio('gameOver', '/static/assets/sounds/patalach.mp3');
        }
        this.load.image('playAgain', '/static/assets/images/playAgain.png');

    },
    create: function() {

        let gameOverSound = this.add.audio('gameOver');
        gameOverSound.play();
        let overText = this.add.text(this.game.width / 2, 50, "Koniec gry", { fill: "green" });
        overText.anchor.set(0.5, 0.5);
        let totalScoreText = this.add.text(this.game.width / 2, 100, `Twój wynik: ${totalScore}`, { fill: "green" });
        totalScoreText.anchor.set(0.5, 0.5);

        //Najlepsze wyniki
        this.hdr = this.add.text(this.game.width / 2, 150, "Najlepsze wyniki", { fill: "gray", fontSize: 18 });
        this.hdr.anchor.set(0.5, 0);
        this.hdr.visible = false;
        this.scoreTable = this.add.text(this.game.width / 2, 200, "nazwa\twynik", { fill: "gray", fontSize: 16, tabs: 200 });
        this.scoreTable.anchor.set(0.3, 0);
        this.scoreTable.visible = false;

        this.playAgainBtn = this.add.button(this.game.width / 2, 400, 'playAgain', this.again, this);
        this.playAgainBtn.anchor.set(0.5, 0);
        this.playAgainBtn.visible = false;

        if (this.topScore) {
            this.nameLabel = this.add.text(this.game.width / 2, 150, "Jesteś w top 5! Podaj swoją nazwę:", { fill: "white" });
            this.nameLabel.anchor.set(0.5, 0);
            this.playerName = this.add.inputField(this.game.width / 2 - 80, 200, {
                font: '16px Arial',
                fill: 'black',
                fontWeight: 'bold',
                width: 150,
                max: 20,
                padding: 8,
                textAlign: 'left',
                borderWidth: 1,
                borderColor: '#FFF',
                borderRadius: 6,
            });
            this.submitBtn = this.add.button(this.game.width / 2, 460, 'submit', this.onSubmit, this);
            this.submitBtn.anchor.set(0.5, 0);
        } else {
            this.showHighScores();
        }


    },
    update: function() {


    },
    onSubmit: function() {
        top5.pop();
        let name = this.playerName.value;
        this.nameLabel.destroy();
        this.playerName.destroy();
        this.submitBtn.destroy();
        for (let i = 0; i < top5.length; i++) {
            if (totalScore > top5[i].score) {
                top5.splice(i, 0, { name: name, score: totalScore });
                break;
            }
            if (i == 3) {
                top5.splice(4, 0, { name: name, score: totalScore });
                break;
            }
        }
        req('/setscore', null, JSON.stringify({ name: name, score: totalScore, _k: gets(name) }));
        this.showHighScores();
    },
    showHighScores: function() {
        let highScores = "";
        try {
            top5.forEach(function(el, idx) {
                highScores += `${el.name}\t${el.score}\n`;
            });
            this.scoreTable.text = highScores;
            this.scoreTable.visible = true;
            this.hdr.visible = true;
            this.playAgainBtn.visible = true;
        } catch (err) {
            console.log("no i się zesrało")
            console.log(err)
        }

    },
    again: function() {
        this.state.start("gameplay");
    }
};


function req(address, callback, data = null) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            if (callback != null) {
                callback(this.responseText);
            }
        }
    };
    xhttp.open("POST", address, false);
    console.log(data);
    xhttp.send(data);
}


function gets(n) {
    c = readCookie('_tr');
    t = sha224(c + sk + totalScore + n)
    return t;
}